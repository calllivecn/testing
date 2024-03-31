#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-19 01:44:24
# author calllivecn <calllivecn@outlook.com>

from tkinter import *

root = Tk()
# root.overrideredirect(True)
root.update()
root.attributes('-alpha', 0.5)


print(root.geometry())

canvas = Canvas(root, bg='white', width=2000, height=1000)
# 这个可以随着窗口大小而变化
# canvas.pack()
canvas.pack(fill="both", expand=True)

rect = canvas.create_rectangle(50, 50, 550, 550, outline='red')

def resize_canvas(e):
    # w = root.winfo_width()
    # h = root.winfo_height()
    canvas.config(width=e.width, height=e.height)

# 窗口大小变化
root.bind('<Configure>', resize_canvas)

def on_button_press(event):
    x1, y1 = canvas.canvasx(event.x), canvas.canvasy(event.y)
    rect_coords = canvas.coords(rect)
    if x1 > rect_coords[0] + 10 and x1 < rect_coords[2] - 10 and y1 > rect_coords[1] + 10 and y1 < rect_coords[3] - 10:
        canvas.bind('<B1-Motion>', on_move)
        canvas.bind('<ButtonRelease-1>', on_button_release)
    else:
        canvas.bind('<ButtonRelease-1>', on_button_release)

def on_move(event):
    canvas.move(rect, event.x - canvas.canvasx(event.x), event.y - canvas.canvasy(event.y))

def on_button_release(event):
    canvas.unbind('<B1-Motion>')
    canvas.unbind('<ButtonRelease-1>')


# canvas.tag_bind(rect, '<ButtonPress-1>', on_button_press)
# canvas.bind('<ButtonPress-1>', on_button_press)

root.mainloop()
