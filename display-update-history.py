#!/usr/bin/python
# -*- coding: utf-8 -*-

import shelve


if __name__ == '__main__':
    db = shelve.open('update-record')
    for key in db.keys():
        print key, db[key]