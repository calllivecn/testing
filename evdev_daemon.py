#!/usr/bin/env python3
#coding=utf-8

from threading import Thread
import evdev
import os
import subprocess

wav_file = '/tmp/1.wav'

CMD = 'aplay {} &> /dev/null'.format(wav_file)

def check_keyboard():
    keyboards = []
    for dev in [ evdev.InputDevice(fn) for fn in evdev.list_devices() ]:
        if 'Keyboard' in dev.name:
            keyboards.append(dev)
    return keyboards


def audio(dev):
    for event in dev.read_loop():
        if event.value == 1 and event.type == 1:
            #print('按下键',evdev.ecodes.KEY[event.code])
            #print(dev.fn,event)
            th_1 = Thread(target=os.system,args=(CMD,))#,daemon=True)
            th_1.start()

def detectInputKey(dev_keyboards):
    while True:
        select([dev], [], [])
        for event in dev.read():
            print("code:%s value:%s" % (event.code, event.value))





if __name__ == '__main__':
    keyboards = check_keyboard()
    #print(keyboards)
    try:
        for dev in keyboards:#detectInputKey()
            th = Thread(target=audio,args=(dev,),daemon=True)
            th.start()
            print('启动:',th.name,'设备:',dev.fn)

    except KeyboardInterrupt:
        print('\rexit.')
        exit(1)
