#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-23 21:53:37
# author calllivecn <calllivecn@outlook.com>


import sys
import queue
import pprint


import av

gen=True

tail10 = queue.Queue(10)

in_v = av.open(sys.argv[1])

def print_dict(obj):
    for proerty in dir(obj):
        if not proerty.startswith("__"):
            print(f"{proerty}:{getattr(obj, proerty)}")

def get_attr(obj):
    """
    获取对象的所有公共属性及其对应的值。
    
    参数:
    obj (object): 要检查的对象
    
    返回:
    dict: 包含对象所有公共属性及其对应值的字典
    """
    attributes = {}
    for attr in dir(obj):
        if not attr.startswith('_'):  # 过滤掉私有属性和特殊方法
            value = getattr(obj, attr)
            if callable(value):  # 过滤掉方法
                attributes[attr] = type(value)
            else:
                attributes[attr] = value
    #return attributes
    pprint.pprint(attributes)

get_attr(in_v)
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
                #print(f"video: keyframe:{packet.is_keyframe} {packet.dts=}  {packet.pts=}")
                get_attr(packet)
            case "audio":
                #print(f"audio: keyframe:{packet.is_keyframe} {packet.dts=}  {packet.pts=}")
                get_attr(packet)

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
