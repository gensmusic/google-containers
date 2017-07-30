#!/usr/bin/python
# -*- coding: utf-8 -*-

import shelve


if __name__ == '__main__':
    db = shelve.open('update-record')
    for source in db.keys():
        info = db[source]
        for tag in info.keys():
            print source, tag, info[tag]