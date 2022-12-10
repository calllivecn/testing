#!/usr/bin/env python3
#coding=utf-8
# date 2018-01-29 18:34:37
# author calllivecn <c-all@qq.com>


import io
import os
import sys
import copy
import wave
# import atexit
import termios
import argparse
from pathlib import Path


import pyaudio

AV_FLAG = True
try:
    import av
except ModuleNotFoundError:
    AV_FLAG = False


class KeyTouch:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        new_settings = copy.deepcopy(self.old_settings)
        new_settings[3] &= ~(termios.ICANON | termios.ECHO) # | termios.ISIG)
        #new_settings[6][termios.VMIN] = 1
        #new_settings[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSADRAIN, new_settings)
    
    def read(self):
        return os.read(self.fd, 16)

    def close(self):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)


class AudioContainer:
    FMT = (".wav", ".mp3", ".aac")
    def __init__(self, format):
        if format in self.FMT:
            self.format = format
        else:
            raise ValueError("format is chioce: *.wav *.mp3 *.aac")
    
        self.file = open()
    


class Audio:

    def __init__(self, output: Path, record_seconds: int = 5):
        self.output = output

        self.format = pyaudio.paInt16
        self.chunk = 8192
        self.channels = 1
        self.rate = 16000
        self.record_seconds = record_seconds

        self.wf = wave.open(self.output, "wb")
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(pyaudio.get_sample_size(self.format))
        self.wf.setframerate(self.rate)

        self.reset()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            #output=True,
            #input_device_index=6,
            start=False,
            frames_per_buffer=self.chunk,
            stream_callback=self.callback)
    
    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def reset(self):
        self.frames = io.BytesIO()

    def callback(self, in_data, frames_count,time_info, status):
        # print(in_data,frames_count,time_info,status)
        # self.frames.write(in_data)
        print(f"{frames_count=} {time_info=} {status=}\r", end="")
        self.wf.writeframes(in_data)
        return (in_data, pyaudio.paContinue)
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        self.wf.close()


DESCRIPTION="按空格键暂停... 按q键停止..."

def main():
    parse = argparse.ArgumentParser(usage="%(prog)s <output.wav>",
    description=DESCRIPTION)

    parse.add_argument("output", action="store", help="指定一个输出文件 *.wav")

    args = parse.parse_args()


    getch = KeyTouch()
    # atexit.register(getch.close)

    pa = Audio(args.output)
    pa.start()

    print(DESCRIPTION)
    status = 1
    while True:
        ch = getch.read()
        if ch == b' ':
            if status == 1:
                pa.stop()
                status = 0
                print('暂停,按空格键继续...')
            else:
                pa.start()
                status = 1
                print('继续...')

        elif ch == b'q':
            print('停止...')
            break
        else:
            print(DESCRIPTION)
    
    pa.close()
    getch.close()


if __name__ == "__main__":
    main()