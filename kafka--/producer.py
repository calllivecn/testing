#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-09 16:06:21
# author calllivecn <calllivecn@outlook.com>


from kafka import KafkaProducer
servers = ["bd05.bnq.in:9092"]

kafka = KafkaProducer(bootstrap_servers=servers)


try:
    while True:
        data = input("> ")
        if data == "exit":
            break
        ok = kafka.send("zx-test", value=data.encode("utf-8"))
        print(ok.get(timeout=3))
except (KeyboardInterrupt, EOFError):
    print("")



