#!/usr/bin/env python3
#coding=utf-8
# date 2018-01-19 20:57:06
# author calllivecn <c-all@qq.com>


import pyaudio
import pprint

pa = pyaudio.PyAudio()

chosen_device_index = -1

for x in range(0, pa.get_device_count()):
    info = pa.get_device_info_by_index(x)
    # pprint.pprint(info)
    pprint.pprint(pa.get_device_info_by_index(x))
    if info["name"] == "pulse":
        chosen_device_index = info["index"]
        print("="*20, f"Chosen index: {chosen_device_index}")

pa.terminate()

#import pyaudio
#p = pyaudio.PyAudio()
#stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input_device_index=chosen_device_index, input=True, output=False)
#stream.start_stream()
