#!/usr/bin/env python3
# coding=utf-8
# date 2020-03-11 11:18:22
# author calllivecn <c-all@qq.com>

import sys
import time 
from tkinter import Tk 

tk = Tk()
tk.title("粘贴板")
print(tk.resizable(0, 0))

x = None
while True:
    # t = tk.selection_get(selection="CLIPBOARD")
    t = tk.clipboard_get()
    print(t)
    if x != t:
        x = t 
        print(t)

        #with open("./tmp.txt", 'a') as f:
        #    timestamp = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        #    f.write(timestamp + '\n' + x + '\n\n')
    time.sleep(1)

win.mainloop()