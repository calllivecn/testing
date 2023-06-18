#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-19 04:52:00
# author calllivecn <c-all@qq.com>

from tkinter import *

root = Tk()

canvas = Canvas(root, width=2000, height=1000)
canvas.pack()

rect = canvas.create_rectangle(50, 50, 550, 550, fill='red')

def on_enter(event):
    canvas.itemconfig(rect, fill='blue')

def on_leave(event):
    canvas.itemconfig(rect, fill='red')

def on_button_press(event):
    canvas.scan_mark(event.x, event.y)

def on_button_motion(event):
    canvas.scan_dragto(event.x, event.y, gain=1)

canvas.tag_bind(rect, '<Enter>', on_enter)
canvas.tag_bind(rect, '<Leave>', on_leave)
canvas.tag_bind(rect, '<Button-1>', on_button_press)
canvas.tag_bind(rect, '<B1-Motion>', on_button_motion)

oval = canvas.create_oval(600, 50, 200, 240, fill="blue")

root.mainloop()

