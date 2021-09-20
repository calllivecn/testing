#!/usr/bin/env python3
# coding=utf-8
# date 2021-08-10 23:18:38
# author calllivecn <c-all@qq.com>

import sys
import time


from aioquic.quic.connection import QuicConnection
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent


def client():
    conf = QuicConfiguration()
    quic = QuicConnection(configuration=conf)
    quic.connect(("::1", 6789), time.time())
    uniqid = quic.get_next_available_stream_id()
    print("uniq id -->", uniqid)
    quic.send_ping(uniqid)

    i=0

    while True:
        data = b"seq:" + str(i).encode()
        print("data -->", data)
        #quic.send_stream_data(uniqid, data)
        quic.send_datagram_frame(data)
        i+=1
        time.sleep(1)


def server():
    conf = QuicConfiguration(is_client=False)
    quic = QuicConnection(conf, ("::1", 6789))

    #while True:
        #quic.receive_datagram

    quic.send_ping()


if __name__ == "__main__":
    if sys.argv[1] == "client":
        client()
    else:
        server()

