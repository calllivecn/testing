#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-10 05:01:34
# author calllivecn <c-all@qq.com>


import io
import os
import sys
import time
import wave
import copy
import termios
import argparse
from pathlib import Path


import pyaudio
import numpy as np

import torch
import whisper

CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = copy.deepcopy(old_settings)
    new_settings[3] &= ~(termios.ICANON | termios.ECHO) # | termios.ISIG)
    #new_settings[6][termios.VMIN] = 1
    #new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(fd,termios.TCSADRAIN,new_settings)
    
    ch = os.read(fd,8)

    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

    return ch

def save(wave_output_filename, wav):
    with wave.open(wave_output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(wav.getbuffer())


DEV = "cuda" if torch.cuda.is_available() else "cpu"
dev = "cpu"
dev = DEV

# model = whisper.load_model("base")
# model = whisper.load_model("small")
# model = whisper.load_model("medium")

# 使用CPU太慢了。。。
# model = whisper.load_model("medium", device="cpu")
model = whisper.load_model("small", device=dev)

class Callback:

    def __init__(self):
        self.reset()

    def callback(self, in_data, frames_count, time_info, status):
        # print(len(in_data), frames_count, time_info, status)
        self.frames.write(in_data)
        return (in_data, pyaudio.paContinue)
    
    def getbuffer(self):
        return self.frames.getbuffer()
    
    def reset(self):
        self.frames = io.BytesIO()


cb = Callback()
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    #output=True,
    #input_device_index=6,
    start=False,
    frames_per_buffer=CHUNK,
    stream_callback=cb.callback)



# stream.start_stream()
print('按空格键开始 或 暂停并转录...','按s键停止...')
status = 0
while True:
    ch = getch()
    if ch == b' ' or ch == b'e':
        if status == 1:
            stream.stop_stream()
            status = 0
            print('按空格键开始 或 暂停并转录(结束时按 e 转录为英语)...','按s键停止...')

            # 转换成 np.ndarry
            if dev == "cpu":
                data = np.frombuffer(cb.getbuffer(), np.int16).flatten().astype(np.float32)
                frames_tensor = torch.Tensor(data)
            else:
                data = np.frombuffer(cb.getbuffer(), np.int16).flatten().astype(np.float32) / 32768.0
                frames_tensor = torch.Tensor(data).to(device=dev)
            

            # 保留下音频
            save("output.wav", cb)
            
            cb.reset()
            start = time.time()
            # 让它自己选择简体或繁体
            # result = model.transcribe(frames_tensor, language="zh")

            # 按e 转录为英语
            if ch == b"e":
                result = model.transcribe(frames_tensor, task="translate", no_speech_threshold=0.4)
            else:
                result = model.transcribe(frames_tensor, no_speech_threshold=0.4)

            end = time.time()
            print(f"翻译耗时: {round(end - start, 2)}/s")
            # print(f"result: {result}")
            print(f'转录文本: {result["text"]}')

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




# save(sys.argv[1])
