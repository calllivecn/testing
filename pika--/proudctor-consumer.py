#!/usr/bin/env python3
# coding=utf-8
# date 2021-09-20 21:03:46
# author calllivecn <calllivecn@outlook.com>

import sys


import pika
from pika import credentials

QUEUE = "hello"


def productor(host, port, user, pw, count=10000):

    cred = pika.PlainCredentials(user, pw)

    params = (
        pika.ConnectionParameters(host="rmq-net1", port=port, credentials=cred),
        pika.ConnectionParameters(host="rmq-net2", port=port, credentials=cred),
        pika.ConnectionParameters(host="rmq-net4", port=port, credentials=cred, connection_attempts=5, retry_delay=1),
    )

    connection = pika.BlockingConnection(params)

    channel = connection.channel()

    channel.queue_declare(queue=QUEUE)

    for _ in range(count):
        channel.basic_publish(exchange="",
            routing_key="hello",
            body="Hello World!"
            )

    print(f"Sent 'Hello World!' 消息 {count} 次")
    connection.close()
 

consumer_count=0

def callback(ch, method, properties, body):
    global consumer_count
    consumer_count +=1
    if consumer_count >= 2000:
        print("args:", type(ch), type(method), type(properties))
        print(f"Received {body.decode()}")
        consumer_count = 0


def consumer(host, port, user, pw):
    
    cred = pika.PlainCredentials(user, pw)

    params = (
        pika.ConnectionParameters(host="rmq-net1", port=port, credentials=cred),
        pika.ConnectionParameters(host="rmq-net2", port=port, credentials=cred),
        pika.ConnectionParameters(host="rmq-net4", port=port, credentials=cred, connection_attempts=5, retry_delay=1),
    )
    connection = pika.BlockingConnection(params)
    
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE)

    channel.basic_consume(on_message_callback=callback,
        queue=QUEUE,
        auto_ack=True,
        )

    print("[*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


def main():

    if sys.argv[1] == "consumer":
        consumer("rmq-net1", 5672, "zx", "zx")
    else:
        productor("rmq-net1", 5672, "zx", "zx")

if __name__ == "__main__":
    main()