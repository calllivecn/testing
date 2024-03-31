#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-18 01:18:58
# author calllivecn <calllivecn@outlook.com>


import time
import threading

import tkinter as tk


root = tk.Tk()
root.title("text")

def get_info():
    print(root.winfo_geometry())


def get_mouse_pos():
    while True:
        print("="*40)
        print("x:", root.winfo_pointerx())
        print("y:", root.winfo_pointery())
        time.sleep(3)


th = threading.Thread(target=get_mouse_pos, daemon=True)
th.start()


btn = tk.Button(root, text="查看窗口位置", command=get_info)
btn.pack()


root.mainloop()
