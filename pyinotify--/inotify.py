#!/usr/bin/env python3
# coding=utf-8
# date 2019-01-07 15:15:25
# https://github.com/calllivecn


import pyinotify 

pi = pyinotify.WatchManager()

pi.add_watch('/tmp', pyinotify.ALL_EVENTS, rec=True)


notify = pyinotify.Notifier(pi, print)
 
notify.loop()
