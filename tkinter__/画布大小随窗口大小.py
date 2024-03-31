#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-20 00:17:55
# author calllivecn <calllivecn@outlook.com>

import tkinter as tk

root = tk.Tk()

root.geometry("1800x1000")

root.update()
print(root.geometry())

canvas = tk.Canvas(root, bg="yellow")
# canvas.pack(fill=tk.BOTH, expand=True)
canvas.pack()

rect = canvas.create_rectangle(50, 50, 550, 550, outline='red')

def resize(event):
    print(f"{event=}")
    print(f"window Pos:", root.geometry())
    canvas.configure(width=event.width, height=event.height)

root.bind("<Configure>", resize)

root.mainloop()

