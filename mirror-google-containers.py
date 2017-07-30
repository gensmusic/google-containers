#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import re
import os
import time
import subprocess
import socket
from datetime import datetime
import shelve
import json

logVerbose = True

class History:
    def __init__(self, filename = 'update-record'):
        self.db = shelve.open(filename)

    def today(self):
        return time.strftime('%Y%m%d')

    def update(self, source, tag, digest, success = True, err = ''):
        taginfo = {'digest': digest, 'date': self.today(), 'ok': success, 'err': err}
        if self.db.has_key(source):
            d = self.db[source]
            d[tag] = taginfo
            self.db[source] = d
        else:
            self.db[source] = {tag : taginfo}
        self.db.sync()

    def shouldUpdate(self, source, tag, digest):
        if not self.db.has_key(source):
            return True
        tagsList = self.db[source]
        if not tagsList.has_key(tag):
            return True
        info = tagsList[tag]
        if info['date'] == self.today() and info['ok'] == True and info['digest'] == digest:
            return False
        return True

    def close(self):
        self.db.close()

def runCommand(args):
    if logVerbose:
        print '=> Run command:', args
    else:
        args += " >/dev/null 2>&1"
    i = subprocess.call(args, shell=True)
    if i != 0 and logVerbose:
        print '=> Failed to runCommand:', args
    return i

def mustRunCommand(args):
    i = runCommand(args)
    if i != 0:
        raise Exception('Failed to runcommand', args)

def mustRunCommandAndGet(args):
    if logVerbose:
        print '=> Run command:', args
 
    # will raise exception when exit code is not 0
    return subprocess.check_output(args, shell=True)

def runCommandAndGet(args):
    try:
        return mustRunCommandAndGet(args)
    except Exception as e:
        return str(e)

class Docker:
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def login(self):
        command = "docker login -u %s -p %s" % (self.username, self.password)
        for i in [2, 4, 8]:
            res = runCommandAndGet(command)
            if 'Login Succeeded' in res:
                if logVerbose:
                    print 'Login Succeeded'
                return
            print 'Login got:%s and retry in %d seconds' %s (res, i)
            time.sleep(i)
        raise Exception('Failed to login docker hub')

    def pull(self, source, all = False):
        print 'pull image:' + source
        command = "docker pull %s %s" % (source, "-a" if all else "")
        mustRunCommand(command)

    def removeAllImages(self):
        command = "docker rmi -f $(docker images -q | uniq)"
        runCommand(command)

    def tag(self, source, target):
        command = "docker tag %s %s" % (source, target)
        mustRunCommand(command)

    def push(self, source):
        print 'push ' + source
        self.login()
        command = "docker push %s" % (source)
        mustRunCommand(command)

def getOriginalTagInfo(image):
    err = None
    for i in [2, 4, 8]:
        try:
            command = "gcloud alpha container images list-tags %s --limit=999 --format=json" % (image)
            res = mustRunCommandAndGet(command)
            res = json.loads(res)
            taglists = []
            for entry in res:
                if not entry.has_key('tags') or not entry.has_key('digest'):
                    print 'Warning:%s has no tags or digest entry:' % (image), entry
                    continue
                tags = entry['tags']
                digest = entry['digest']
                if not isinstance(tags, list) or len(digest) == 0:
                    print 'Warning:%s bad tags or digest:' % (image), entry
                    continue
                if len(tags) == 0:
                    continue
                for tag in tags:
                    taglists.append({'tag': tag, 'digest': digest})
            return taglists
        except Exception as e:
            err = e
            print 'getOriginalTagInfo got error:%s and retry in %d seconds' % (str(e), i)
            time.sleep(i)
    if err is not None:
        raise Exception(str(err))
    return []


def transport(images, docker, history):
    for source in images:
        tagslist = getOriginalTagInfo(source)
        if len(tagslist) == 0:
            print 'Found no tags for ' + source
            continue
        # clean
        docker.removeAllImages()

        for taginfo in tagslist:
            tag = taginfo['tag']
            digest = taginfo['digest']
            if not history.shouldUpdate(source, tag, digest):
                print '%s %s %s NO need to update' % (source, tag, digest)
                continue

            reponame = source.split('/')[-1]
            fromImage = "%s:%s" % (source, tag)
            toImage = "mirrorgooglecontainers/%s:%s" % (reponame, tag)
            print 'Start mirror %s to %s' % (fromImage, toImage)

            err = None
            for i in [10, 20, 30]:
                try:
                    docker.pull(fromImage)
                    docker.tag(fromImage, toImage)
                    docker.push(toImage)
                    break
                except Exception as e:
                    err = e
                    print '%s got err:%s, retry in %d seonds' % (source, str(e), i)
                    time.sleep(i)
            # record update history
            ok = True if err is None else False
            history.update(source, tag, digest, ok, str(err))

def getImages():
    with open('google-containers-images.list') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("username", help="target registry login username")
    parser.add_argument("password", help="target registry login password")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    logVerbose = args.verbose

    # user root
    if os.getuid() != 0:
        print '!' * 50
        print '  Please run with sudo since we need to run docker'
        print '!' * 50
        exit(1)


    print 'Started...' + str(datetime.now())

    images = getImages()
    history = History()
    docker = Docker(args.username, args.password)
    transport(images, docker, history)

    print 'Finished...' + str(datetime.now())
