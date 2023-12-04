#!/usr/bin/env python3
# coding=utf-8
# date 2022-10-31 20:13:16
# author calllivecn <c-all@qq.com>

import os

from miio import Device

IP = os.environ["MIROBO_IP"]
TOKEN = os.environ["MIROBO_TOKEN"]

def info():
    #s = miio.device.Device(ip=IP, token=TOKEN)
    s = Device(ip=IP, token=TOKEN)
    print(s.info())

"""
这里查看怎么使用这个设备:
Out: chuangmi.plug.m3 v1.3.8_0002 (04:CF:8C:5F:**:**) @ 192.168.1.20 - token: *****
我们可以得到设备的模块名称为：chuangmi.plug.m3

查看miio目录中的chuangmi_plug.py文件，可以看到对应的Class ChuangmiPlug。

"""

info()

############## 我是分割线 ######################

from miio.chuangmi_plug  import ChuangmiPlug

d = ChuangmiPlug(ip=IP, token=TOKEN)

x=d.status() # 给出设备的状态

print(f"status() --> {x}")
# x: <ChuangmiPlugStatus power=True, usb_power=None, temperature=46, load_power=None, wifi_led=None>
# x.power = True

exit(0)

print(f"led: {d.led()}")

if x.is_on:
    x=d.off()
    print(f"off() --> {x}")
else:
    x=d.on()
    print(f"on() --> {x}")

# x = ['ok'] 则 控制成功
#x=d.on()
#print(f"on() {x}")
# x = ['ok'] 则 控制成功
