#!/usr/bin/env python3
# coding=utf-8
# date 2019-09-25 10:36:46
# author calllivecn <c-all@qq.com>


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

if __name__ == "__main__":
    w, h = get_display_resolvtion()
    print("分辨率：宽：{} 高：{}".format(w, h))
    w, h = get_display_realsize()
    print("物理宽：{}mm 物理高：{}mm".format(w, h))


