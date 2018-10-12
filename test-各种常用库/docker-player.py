#!/usr/bin/env py3
#coding=utf-8
# date 2018-08-30 16:05:31
# author calllivecn <c-all@qq.com>

import pprint
import json

import docker

#cli = docker.DockerClient(base_url="unix:///var/run/docker.sock")
cli = docker.DockerClient(base_url="tcp://192.168.224.174:9527")

for con_id in cli.containers.list():
    print(con_id.id,con_id.name)
    inspect = cli.api.inspect_container(con_id.id)
    #pprint.pprint(inspect)
    mem=inspect['HostConfig']['Memory']
    print(float(mem)/1024/1024,"MB")




for con_id in cli.containers.list():
    print(con_id.id,con_id.name)
    inspect = con_id.stats(stream=False, decode=True)
    #pprint.pprint(inspect)
    mem=inspect.get("memory_stats").get("usage")
    print(float(mem)/1024/1024,"MB")
