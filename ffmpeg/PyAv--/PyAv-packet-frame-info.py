#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-23 21:53:37
# author calllivecn <calllivecn@outlook.com>


import sys
import queue


import av

gen=True

tail10 = queue.Queue(10)

for i, packet in enumerate(in_v.demux()):
    if gen:
        print(f"{i=} {packet.is_keyframe=} {packet=}")
    else:
        if i < 10:
            print(f"{i=} {packet.is_keyframe=} {packet=}")

    if tail10.full():
        tail10.get()

    tail10.put((i, packet))

print(f"="*20)

while not tail10.empty():
    i, packet = tail10.get()
    print(f"{i=} {packet.is_keyframe=} {packet=}")
