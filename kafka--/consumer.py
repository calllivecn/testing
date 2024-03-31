#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-03 17:38:12
# author calllivecn <calllivecn@outlook.com>


from kafka import KafkaConsumer
from kafka import KafkaProducer


servers = ["bd05.bnq.in:9092"]


consumer = KafkaConsumer("NginxLog", auto_offset_reset="earliest", bootstrap_servers=servers)

print("consumer type: ", type(consumer), "print(consumer):", consumer)

c = 0
for data in consumer:
    c+=1
    print("第{}条消息：{}".format(c, data.value.decode("utf-8")))
