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

registryUser = ""
registryPswd = ""

class History:
    def __init__(self, filename = 'update-record'):
        self.db = shelve.open(filename)

    def today(self):
        return time.strftime('%Y%m%d')

    def update(self, source, success = True):
        self.db[source] = {'date': self.today(), 'ok': success}
        self.db.sync()

    def hasUpdatedToday(self, source):
        if self.db.has_key(source):
            record = self.db[source]
            if record['date'] == self.today() and record['ok'] == True:
                return True
        return False

    def close(self):
        self.db.close()

def runCommand(args, verbose = True):
    if verbose:
        print '=> Run command:', args
    i = subprocess.call(args, shell=True)
    if i != 0:
        print '=> Failed to runCommand:', args
    return i

def mustRunCommand(args, verbose = True):
    if verbose:
        print '=> Run command:', args
    i = subprocess.call(args, shell=True)
    if i != 0:
        raise Exception('Failed to runcommand', args)

def runCommandAndGet(args, verbose = True):
    if verbose:
        print '=> Run command:', args
    try:
        return subprocess.check_output(args, shell=True)
    except Exception as e:
        return str(e)

def loginDockerHub():
    command = "docker login -u %s -p %s" % (registryUser, registryPswd)

    for i in [2, 4, 8]:
        res = runCommandAndGet(command, False)
        if 'Login Succeeded' in res:
            print 'Login Succeeded'
            return True
        
        print 'Login got:' + res
        print 'try in %d seconds' % i
        time.sleep(i)

    raise Exception('Failed to login docker hub')

def transport(images, history):
    for source in images:
        if history.hasUpdatedToday(source):
            print '%s has updated today!' % (source)
            continue

        reponame = source.split('/')[-1]
        target = "mirrorgooglecontainers/%s" % (reponame)
        print 'Start mirror %s to %s' % (source, target)

        command = "docker rmi -f $(docker images -q | uniq)"
        runCommand(command)

        updateOK = False
        for i in [10, 20, 40]:
            try:
                command = "docker pull %s -a" % (source)
                mustRunCommand(command)

                command = "docker images | grep %s | awk '{print $2}'" % (source)
                res = runCommandAndGet(command)
                tags = res.strip().split('\n')
                if len(tags) == 0:
                    print 'Found no tags for ' + source
                    break
                for tag in tags:
                    command = "docker tag %s:%s %s:%s" % (source, tag, target, tag)
                    mustRunCommand(command)
                    loginDockerHub()
                    command = "docker push %s:%s" % (target, tag)
                    mustRunCommand(command)
                updateOK = True
                break
            except Exception as e:
                print '%s got err:%s, retry in %d seonds' % (source, str(e), i)
                time.sleep(i)
        # record update history
        history.update(source, updateOK)

def getImages():
    with open('google-containers-images.list') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("username", help="target registry login username")
    parser.add_argument("password", help="target registry login password")

    args = parser.parse_args()

    registryUser, registryPswd = args.username, args.password

    # user root
    if os.getuid() != 0:
        print '!' * 50
        print '  Please run with sudo since we need to run docker'
        print '!' * 50
        exit(1)

    # login(registry, username, password)

    images = getImages()
    history = History()
    transport(images, history)
