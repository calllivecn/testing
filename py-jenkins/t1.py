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

job = server.get_job_config("test_jks_time")

pprint(user)
print("-"*60)
pprint(version)

print("-"*60)

true_false = server.job_exists("test_jks_time3")
print(true_false)
print("-"*60)

building_list = server.get_running_builds()
pprint(building_list)
print("-"*60)


config_xml = server.get_job_config("test_jks_time")
pprint(config_xml)
print("-"*60)
