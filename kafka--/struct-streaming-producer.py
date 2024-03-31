#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-04 11:17:33
# author calllivecn <calllivecn@outlook.com>

import time
from functools import partial

from kafka import KafkaProducer

servers = ["bd05.bnq.in:9092"]

jks_access_log = "/home/zx/bigdata/pyspark/jks_access.log"

producer = KafkaProducer(bootstrap_servers=servers)
print("producer type: ", type(producer), "print(producer):", producer)


with open(jks_access_log, "rb") as f:
    for line in iter(partial(f.readline), b""):
        future = producer.send("NginxLog", value=line)
        print("result:", future.get(timeout=3), "line: ", line)
        time.sleep(1)



