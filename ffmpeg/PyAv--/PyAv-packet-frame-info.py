#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-23 21:53:37
# author calllivecn <calllivecn@outlook.com>


import sys
import queue


import av

gen=True

tail10 = queue.Queue(10)

in_v = av.open(sys.argv[1])

def print_dict(obj):
    for proerty in dir(obj):
        if not proerty.startswith("__"):
            print(f"{proerty}:{getattr(obj, proerty)}")

print_dict(in_v)
print("-"*40)

for i, packet in enumerate(in_v.demux()):
    if gen:
        print("="*40)

        #print(f"{i=} {packet.stream.time_base=} {packet.duration=} {packet.time_base=} {int(packet.duration * packet.time_base)=}")
        #print(f"{i=} keyframe:{packet.is_keyframe} type:{packet.stream.type} {packet=} {dir(packet)=}")
        #print_dict(packet)
        #print("-"*40, "stream", "-"*40)
        #print_dict(packet.stream)

        match packet.stream.type:
            case "video":
                print(f"video: keyframe:{packet.is_keyframe} {packet.dts=}  {packet.pts=}")
            case "audio":
                print(f"audio: keyframe:{packet.is_keyframe} {packet.dts=}  {packet.pts=}")

            case _:
                print(f"未知类型: {packet=}")


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
