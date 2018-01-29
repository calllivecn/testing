#!/usr/bin/env python3
#coding=utf-8
# date 2018-01-29 18:34:37
# author calllivecn <c-all@qq.com>


"""PyAudio example: Record a few seconds of audio and save to a WAVE file."""
import struct
import array
import wave
import time

import libpy

import pyaudio
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

def save(wave_output_filename="output.wav"):
    with wave.open(wave_output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

# 过滤小声音
# 事实证明没用～～～,这样破坏了完整声音。
def voice(voice_data):
    voice = struct.Struct("<h")
    data = []
    for v in array.array("h",voice_data):
        if 5000 <= v:
            data.append(voice.pack(v))
    return data



frames = []
def callback(in_data, frames_count,time_info, status):
    #print(in_data,frames_count,time_info,status)
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    #output=True,
    #input_device_index=6,
    frames_per_buffer=CHUNK,
    stream_callback=callback)


print('按空格键暂停...','按s键停止...')
stream.start_stream()

status = 1
while True:
    ch = libpy.getch()
    if ch == b' ':
        if status == 1:
            stream.stop_stream()
            status = 0
            print('暂停,按空格键继续...')
        else:
            stream.start_stream()
            status = 1
            print('继续...')

    elif ch == b's':
        stream.stop_stream()
        stream.close()
        p.terminate()
        print('停止...')
        break
    else:
        print('请按空格键暂停或按s键停止...')


#stream.stop_stream()
#stream.close()
#p.terminate()

#with open('output.pcm','w+b') as wf:
#    wf.write(b''.join(frames))

save('output.wav')
