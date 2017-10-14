#!/bin/sh


./display-update-history.py > update-history.txt
git add .
git commit -m 'update history'
git push origin master

