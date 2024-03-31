#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-18 23:54:11
# author calllivecn <calllivecn@outlook.com>

import httpx


BUFSIZE=4096

def test1():
    client = httpx.Client(http2=True)

    # stream 是一个contextlib.manager; stream.gen 是一个 generator
    stream = client.stream("GET", "https://launcher.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar")
    # next() 启动这个 generator
    response = next(stream.gen)
    for chunk in response.iter_bytes(BUFSIZE):
        print(type(chunk), len(chunk))
    print("next(stream.gen):", type(response))

    client.close()


def test2():
    client = httpx.Client(http2=True)
    # 这样是可以的
    with client.stream("GET", "https://launcher.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar") as stream:
        for chunk in stream.iter_bytes(BUFSIZE):
            print(type(chunk), len(chunk))

    client.close()

if __name__ == "__main__":
    test1()
    #test2()
