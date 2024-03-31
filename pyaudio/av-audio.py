#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-11 22:05:17
# author calllivecn <calllivecn@outlook.com>


AV_FLAG = True
try:
    import av
except ModuleNotFoundError:
    AV_FLAG = False

fps = 16000

options = {"bit_rate": 24000}

container = av.open('test.aac', mode='w')
# container = av.open('test.mkv', mode='w')
audio0 = container.add_stream('aac', rate=fps)


# audio0.channel = 1


for i in range(4096):
    frame = av.AudioFrame(i)
    for packet in audio0.encode(frame):
        container.mux(packet)


for packet in audio0.encode():
    container.mux(packet)

container.close()


