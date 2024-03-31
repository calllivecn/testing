#!/usr/bin/env py3
#coding=utf-8
# date 2018-09-13 09:39:03
# author calllivecn <calllivecn@outlook.com>

import pika


con = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

channel = con.channel()

#channel.queue_declare(queue='hello')
channel.queue_declare(queue='task_queue',durable=True)

while True:
    try:
        msg = input("输入消息：")
    except KeyboardInterrupt:
        print("退出")
        break

    #channel.basic_publish(exchange="",routing_key="hello",body="hello world!")
    #channel.basic_publish(exchange="",routing_key="hello",body=msg.encode())
    channel.basic_publish(exchange="",routing_key="task_queue",body=msg.encode(),properties=pika.BasicProperties(delivery_mode=2))

    print('[x]发送"Hello World!"')

con.close()
