#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-23 17:19:21
# author calllivecn <calllivecn@outlook.com>


import jenkins

import time
from pprint import pprint

import pw


JOB="autopilot-dev"

server = jenkins.Jenkins('http://jks.bnq.in', username=pw.USERNAME, password=pw.PASSWORD)


#queue_id = server.build_job("autopilot-dev", {"branch": "dev", "release_id": 99999999999999999999})
#print(queue_id)
#exit(0)

"""
queue_id = 7754
build_id = 2

try:
    queue_id_info = server.get_queue_item(queue_id)
except jenkins.JenkinsException as e:
    print(False, e)
    exit(1)

print("-"*60)
pprint(queue_id_info)
print("-"*60)


try:
    task_name = queue_id_info["task"]["name"]
except KeyError as e:
    print(False, e)
    exit(2)

print("task name :", task_name)

try:
    build_id = queue_id_info["number"]
except KeyError as e:
    print(False, e)
    exit(2)
"""

jks_name="test_jks_time"

#build_id = server.get_job_info(jks_name)['nextBuildNumber']
#server.build_job(jks_name,{"release_id": 9999})
#print("build id:", build_id)

build_id = 39
while True:

    queue_info = server.get_queue_info()
    print("TYPE --> ",type(queue_info))
    pprint(queue_info)
    wait_queue = []
    for info in queue_info:
        try:
            name = info["task"]["name"]
            print(name)
            wait_queue.append(name)
        except KeyError:
            print("Key error")
            continue

    print(wait_queue)
    if jks_name in wait_queue:
        print("{} 在等待队列中...".format(jks_name))
        time.sleep(3)
        continue

    try:
        build_info = server.get_build_info(jks_name, build_id)
    except jenkins.JenkinsException as e:
        print(False, e)
        exit(3)
    
    building = build_info.get("building")
    result = build_info.get("result")

    if building == True:
        print("还在构建当中")

    else:
        
        if result == "FAILURE":
            print("构建失")
            break
        
        elif result == "SUCCESS":
            duration = build_info.get("duration")
            print("构建用时: ", duration)
            break
        
        elif result == "ABORTED":
            duration = build_info.get("duration")
            print("取消构建，构建用时: ", duration)
            break
        
        else:
            print("未知情况")
            break

    time.sleep(3)
    
    print(result)
    pprint(build_info)



print(result)
pprint(build_info)
