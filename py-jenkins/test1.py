#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-25 10:43:11
# author calllivecn <c-all@qq.com>

import json
from pprint import pprint


import jenkins
import etcd


import pw

e = etcd.Client("192.168.224.172",2379)

jks = jenkins.Jenkins('http://jks.bnq.in', username=pw.USERNAME, password=pw.PASSWORD)

jks_name="test_jks_time"

release_id = 316

jks_info = jks.get_job_info(jks_name)
pprint(jks_info)

build_id = jks_info["nextBuildNumber"]


jks.build_job(jks_name, {"param1": "测试测试测试～～～～"})


def write_etcd(release_id, jks_name, build_id):

    data = json.dumps({"release_id": release_id, "build_id": build_id})

    e.write("/jenkinsjob/" + jks_name, data)



write_etcd(release_id, jks_name, build_id)

#e.write("/jenkinsjob/" + jks_name, data)


