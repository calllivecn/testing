#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-23 17:05:53
# author calllivecn <calllivecn@outlook.com>

from pprint import pprint

import jenkins

import pw


server = jenkins.Jenkins('http://jks.bnq.in', username=pw.USERNAME, password=pw.PASSWORD)


jobs = [ "test_jks_time1", "test_jks_time2", "test_jks_time3", "test_jks_time4", "test_jks_time"]



for j in jobs:
    print(j)
    server.build_job(j, {"release_id": 9999})

print("done")
