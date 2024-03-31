#!/usr/bin/env python3
# coding=utf-8
# date 2019-05-15 17:23:25
# author calllivecn <calllivecn@outlook.com>


import hdfs

cli = hdfs.Client("http://192.168.56.6:9870")

for l in cli.list("/",True):
    print(l)
