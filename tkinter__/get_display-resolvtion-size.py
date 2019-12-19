#!/usr/bin/env python3
# coding=utf-8
# date 2019-09-25 10:36:46
# author calllivecn <c-all@qq.com>

import math
import tkinter

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

def get_ppi(w, h, rw, rh):
    # 1米 = 39.3700787英寸
    i = 39.3700787
    s = w**2 + h**2
    l = math.sqrt(s)
    rs = rw**2 + rh**2
    rl = math.sqrt(rs)

    in_ = rl/1000*i

    return in_

if __name__ == "__main__":

    w, h = get_display_resolvtion()
    print("分辨率宽：{} 高：{}".format(w, h))

    rw, rh = get_display_realsize()
    print("物理宽：{}mm 高：{}mm".format(rw, rh))

    ppi = get_ppi(w, h, rw, rh)
    print("PPI(每英寸像素)：", round(ppi, 3))


