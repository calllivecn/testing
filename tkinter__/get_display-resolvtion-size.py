#!/usr/bin/env python3
# coding=utf-8
# date 2019-09-25 10:36:46
# author calllivecn <c-all@qq.com>

import math
import tkinter

# 1米 = 39.3700787英寸
IN_METER = 39.3700787

def get_display_resolvtion():
    """
    return: width, wicth
    """
    win = tkinter.Tk()
    height = win.winfo_screenheight()
    width  = win.winfo_screenwidth()

    return width, height


def get_display_realsize():
    """
    return: width, wicth
    """
    win = tkinter.Tk()
    height = win.winfo_screenmmheight()
    width  = win.winfo_screenmmwidth()

    return width, height

# 屏幕尺寸(对角线长度)单位英寸
def get_size_IN(rw, rh):
    rs = rw**2 + rh**2
    rl = math.sqrt(rs)
    in_ = rl/1000*IN_METER
    return in_

def get_ppi(w, h, rw, rh):
    s = w**2 + h**2
    l = math.sqrt(s)

    rs = rw**2 + rh**2
    rl = math.sqrt(rs)

    in_ = rl/1000*IN_METER

    return l/in_


if __name__ == "__main__":

    w, h = get_display_resolvtion()
    print("分辨率宽：{} 高：{}".format(w, h))

    rw, rh = get_display_realsize()
    print("物理宽：{}mm 高：{}mm".format(rw, rh))

    display_in = get_size_IN(rw, rh)
    print("显示尺寸(英寸)：", round(display_in, 3))

    ppi = get_ppi(w, h, rw, rh)
    print("PPI(每英寸像素)：", round(ppi, 3))

