#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-23 17:05:53
# author calllivecn <c-all@qq.com>

from pprint import pprint

import jenkins

import pw


server = jenkins.Jenkins('http://jks.bnq.in', username=pw.USERNAME, password=pw.PASSWORD)

user = server.get_whoami()

version = server.get_version()

pprint(user)
print()
pprint(version)


