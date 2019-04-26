#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-25 10:43:11
# author calllivecn <c-all@qq.com>

import json


import jenkins
import etcd


import pw

e = etcd.Client("192.168.224.172",2379)

#jks = jenkins.Jenkins('http://jks.bnq.in', username=pw.USERNAME, password=pw.PASSWORD)

jks_name="yingxiao_test_market_admin"

release_id = 310

#jks.build_job(jks_name, {"param1": "测试测试测试～～～～"})


def write_etcd(release_id, jks_name, build_id):

    data = json.dumps({"release_id": release_id, "build_id": build_id})

    e.write("/jenkinsjob/" + jks_name, data)



#write_etcd(release_id, jks_name, 7)
data = json.dumps({"release_id": 313, "build_id": 17})

e.write("/jenkinsjob/" + jks_name, data)


