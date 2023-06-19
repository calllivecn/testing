#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-19 01:44:24
# author calllivecn <c-all@qq.com>

"""
0. 实现在画布中画一个矩形
1. 鼠标左键在矩形内按下时可以拖动矩形，改变矩形在画布中的位置。
2. 在鼠标在矩形四边附近时，可以调整矩形大小。(鼠标这时需要改变外形，提示用户可以调整大小。)
"""

# 文档
"""

if len(canvas.find_overlapping(x1-10,y1-10,x2+10,y2+10)) > 1:
        canvas.config(cursor='sb_diagonal_double_arrow')
    else:
        canvas.config(cursor='arrow')

```
在Tkinter中，您可以使用cursor参数来配置鼠标的外形。以下是一些常用的鼠标外形名称：

arrow
circle
clock
cross
dotbox
exchange
fleur
heart
man
mouse
pirate
plus
shibuya # 没有
spider
spraycan
star
target
```
"""




import tkinter as tk
from tkinter import ttk


class Canvas_Rectangle:
    
    def __init__(self):

        self.root = tk.Tk()

        self.canvas = tk.Canvas(self.root, bg='white', width=1620, height=980)
        self.canvas.pack()

        self.canvas.update()

        # 这里还是无效呀！
        self.root.attributes('-alpha', 0.7)

        # 需要查询画布大小(玩家可能使用调整)
        self.w = self.canvas.winfo_width()
        self.h = self.canvas.winfo_height()
        print(f"画布大小: {self.w}x{self.h}")

        # 初始矩形坐标
        self.rect_x0 = 20
        self.rect_y0 = 20
        self.rect_x1 = 220
        self.rect_y1 = 220

        self.x0 =0
        self.y0 =0

        self.entry_rect = False

        self.resize_rect_flag = True

        # 画布一个20像素的矩形看看有多宽
        tmp = self.canvas.create_rectangle(100, 100, 120, 200, width=10, outline='green')

        # 画线宽度
        self.outline_width = 5
        # 这里坐标是矩形的左上角和右下角坐标
        self.rect = self.canvas.create_rectangle(self.rect_x0, self.rect_y0, self.rect_x1, self.rect_y1, width=self.outline_width, outline='red')

        self.mouseDown_funcid = self.canvas.bind("<Button-1>", self.mouseDown)
        self.mouseUp_funcid = self.canvas.bind("<ButtonRelease-1>", self.mouseUp)

        # self.canvas.tag_bind(self.rect, "<Button-1>", self.mouseDown)
        # self.canvas.tag_bind(self.rect, "<B1-Motion>", self.move_rect)
        self.canvas.tag_bind(self.rect, "<Enter>", self.mouse_enter)
        self.canvas.tag_bind(self.rect, "<Leave>", self.mouse_restore)


        # self.canvas.tag_bind(self.rect, "<Button-1>", self.on_button_press)
        # self.canvas.tag_bind(self.rect, "<B1-Motion>", self.move_rect2)
    
    """
    def on_button_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def move_rect2(self, e):
        # 这玩意儿，会移动画布上的所有内容。。。
        self.canvas.scan_dragto(e.x, e.y, gain=1)
    """
    
    def mouse_enter(self, e):
        self.rect_x0, self.rect_y0 = e.x, e.y

        print(f"鼠标进入, {e=}")
        self.canvas.config(cursor='target')
        self.resize_rect_flag = True

        self.canvas.unbind("<Button-1>", self.mouseDown_funcid)
        self.canvas.unbind("<ButtonRelease-1>", self.mouseUp_funcid)

        slef.resize_rect_fundis = self.canvas.tag_bind(self.rect, "<B1-Motion>", self.resize_rect)
        
        # 叉叉
        # self.canvas.config(cursor='pirate')
        
        # 四向箭头
        # self.canvas.config(cursor='fleur')

        # 这个像个方形准心, 和 target 一样？。
        # self.canvas.config(cursor='dotbox')

    
    def mouse_restore(self, e):
        print(f"鼠标离开, {e=}")
        self.canvas.config(cursor='arrow')

        self.resize_rect_flag = False

        self.canvas.tag_unbind(self.rect, "<B1-Motion>")
        

        self.mouseDown_funcid = self.canvas.bind("<Button-1>", self.mouseDown)
        self.mouseUp_funcid = self.canvas.bind("<ButtonRelease-1>", self.mouseUp)

    
    def mouseDown(self, e):
        # 矩形上次的位置
        self.x0, self.y0 = e.x, e.y
        print(f"鼠标按下，拿到矩形位置", self.x0, self.y0)

        # 检测鼠标是否移动了到矩形上(就是边上)
        # if self.rect in self.canvas.find_overlapping(e.x, e.y, e.x+1, e.y+1):
            # print("鼠标移动到了矩形内部.")

        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        # 使用坐标自己判断
        if x0 + self.outline_width < e.x < x1 + self.outline_width and y0 - self.outline_width < e.y < y1 - self.outline_width:
            print("鼠标在矩形内部.")
            self.entry_rect = True
            self.move_rect_funcid = self.canvas.bind("<B1-Motion>", self.move_rect)
        
        elif not self.rect in self.canvas.find_overlapping(x0 - pos_range, y0 - pos_range, x0 + pos_range, y0 + pos_range):
            self.resize_rect_funcid = self.canvas.bind("<B1-Motion>", self.resize_rect)

    

    def mouseUp(self, e):
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        if x0 + self.outline_width < e.x < x1 + self.outline_width and y0 - self.outline_width < e.y < y1 - self.outline_width:
            self.canvas.unbind("<B1-Motion>", self.resize_rect_funcid)
            self.entry_rect = False

        # 只要不是在矩形内就是外面
        elif not self.rect in self.canvas.find_overlapping(x0 - pos_range, y0 - pos_range, x0 + pos_range, y0 + pos_range):
            self.canvas.unbind("<B1-Motion>", self.move_rect_funcid)
        

    def resize_rect(self, event):
        x0, y0, x1, y1 = self.canvas.coords(self.rect)

        pos_range = 10

        # 左上
        if self.rect in self.canvas.find_overlapping(x0 - pos_range, y0 - pos_range, x0 + pos_range, y0 + pos_range):
            self.canvas.coords(self.rect, event.x, event.y, x1, y1)

        # 右下
        elif self.rect in self.canvas.find_overlapping(x1 - pos_range, y1 - pos_range, x1 + pos_range, y1 + pos_range):
            self.canvas.coords(self.rect, x0, y0, event.x, event.y)
        

    def move_rect(self, event):

        print(f"{event.x=}, {event.y=}")
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        print(f"鼠标在画布上的坐标：{x=} {y=}")

        # 矩形上次的位置
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        print(f"当前矩形位置：", x0, y0, x1, y1)

        # 矩形本身的大小
        rect_x_move_area = self.w - (x1 - x0)
        rect_y_move_area = self.h - (y1 - y0)

        move_x = event.x - self.x0
        move_y = event.y - self.y0

        # 如果已经璚画布边界，就不在移动。
        if x0 + move_x <= 0:
            move_x = 0
        elif x0 + move_x >= rect_x_move_area:
            move_x = 0
        
        if y0 + move_y <= 0:
            move_y = 0
        elif y0 + move_y >= rect_y_move_area:
            move_y = 0

        # 这里的 x y 是相对移动的像素。
        # self.canvas.move(self.rect, event.x - self.x0, event.y - self.y0)
        self.canvas.move(self.rect, move_x, move_y)

        # 最后需要保存本次鼠标位置，供下次移动事件使用
        self.x0, self.y0 = event.x, event.y


    def loop(self):
        self.root.mainloop()


root = Canvas_Rectangle()
root.loop()
