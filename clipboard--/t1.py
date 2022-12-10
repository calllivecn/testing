#!/usr/bin/env python3
# coding=utf-8
# date 2020-03-11 11:18:22
# author calllivecn <c-all@qq.com>

import sys
import time 
import tkinter as tk

r=tk.Tk()
r.withdraw() #隐藏窗口

st=r.clipboard_get() #获取剪贴板内容

print("粘贴板内容: \n", st)

r.clipboard_clear() #清除剪贴板内容

r.clipboard_append("#向剪贴板追加内容")

time.sleep(5)
r.destroy()

