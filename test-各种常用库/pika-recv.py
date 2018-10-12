#!/usr/bin/env py3
#coding=utf-8
# date 2018-09-13 09:43:38
# author calllivecn <c-all@qq.com>

import time
import random

import pika

con = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

channel = con.channel()

#channel.queue_declare(queue='hello')
channel.queue_declare(queue='task_queue',durable=True)

def callblock(ch, method, properties, body):
    print('[x] Received ',body.decode())
    time.sleep(random.randint(1,5))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print("完成")

channel.basic_qos(prefetch_count = 1)

#channel.basic_consume(callblock, queue='hello', no_ack=True)
#channel.basic_consume(callblock, queue='hello')
channel.basic_consume(callblock, queue='task_queue')

print('[*] 等待消息。按CTRL+C退出。')

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("退出")
    con.close()
