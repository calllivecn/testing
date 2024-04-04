#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-19 01:44:24
# author calllivecn <calllivecn@outlook.com>

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
dotbox # 这个像个方形准心, 和 target 一样？。
exchange
fleur # 四向箭头
heart
man
mouse
pirate # 叉叉
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

        # 在ubuntu22.04 wayland 有效果了。
        # self.root.attributes('-alpha', 0.7)

        # 需要查询画布大小(玩家可能使用调整)
        self.w = self.canvas.winfo_width()
        self.h = self.canvas.winfo_height()
        print(f"画布大小: {self.w}x{self.h}")

        # 初始矩形坐标
        self.rect_x0 = 20
        self.rect_y0 = 20
        self.rect_x1 = 220
        self.rect_y1 = 220

        self.x0 = 0
        self.y0 = 0

        self.pos_range = 20

        self.left_up = self.right_down = False

        # 画线宽度
        self.outline_width = 1

        # 这里坐标是矩形的左上角和右下角坐标
        self.rect = self.canvas.create_rectangle(self.rect_x0, self.rect_y0, self.rect_x1, self.rect_y1, width=self.outline_width, outline='red')

        self.mouseDown_funcid = self.canvas.bind("<Button-1>", self.mouseDown)
        self.mouseUp_funcid = self.canvas.bind("<ButtonRelease-1>", self.mouseUp)

        self.mouse_enter_id = self.canvas.tag_bind(self.rect, "<Enter>", self.mouse_enter)
        self.mouse_restore_id =  self.canvas.tag_bind(self.rect, "<Leave>", self.mouse_restore)


    def mouse_enter(self, e):
        self.rect_x0, self.rect_y0 = e.x, e.y

        print(f"鼠标进入, {e=}")

        x0, y0, x1, y1 = self.canvas.coords(self.rect)

        # self.left_up_id = self.canvas.create_oval(x0 - self.pos_range, y0 - self.pos_range, x0 + self.pos_range, y0 + self.pos_range, fill='white', state="disabled")
        # self.right_down_id = self.canvas.create_oval(x1 - self.pos_range, y1 - self.pos_range, x1 + self.pos_range, y1 + self.pos_range, fill='white', state="disabled")

        # self.canvas.tag_lower(self.left_up_id, self.rect)
        # self.canvas.tag_lower(self.right_down_id, self.rect)

        # 检测鼠标是否在左上+右下
        self.left_up = abs(e.x - x0) <= self.pos_range and abs(e.y - y0) <= self.pos_range
        self.right_down = abs(e.x - x1) <= self.pos_range and abs(e.y - y1) <= self.pos_range

        # 只在左上+右下生成提示圆
        if self.left_up or self.right_down:
            self.canvas.config(cursor='target')
            self.resize_rect_fundis = self.canvas.bind("<B1-Motion>", self.resize_rect)
        
        else:
            print("没有到正确位置")
        
    
    def mouse_restore(self, e):

        print(f"鼠标离开, {e=}")
        self.canvas.config(cursor='arrow')

        self.canvas.tag_unbind(self.rect, "<B1-Motion>")
        
        if hasattr(self, "left_up_id"):
            self.canvas.delete(self.left_up_id)
            self.canvas.delete(self.right_down_id)
        

    def mouseDown(self, e):
        # 矩形上次的位置
        self.x0, self.y0 = e.x, e.y

        # 左上+右下检测
        # 检测某个组件是否绑定了指定事件
        if self.left_up or self.right_down:
            if self.canvas.tag_bind(self.rect, '<Enter>'):
                self.canvas.tag_unbind(self.rect, "<Enter>", self.mouse_enter_id)
                self.canvas.tag_unbind(self.rect, "<Leave>", self.mouse_restore_id)
                print("unbind self.rect")

        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        # 使用坐标自己判断,鼠标是否在矩形内部
        if x0 + self.pos_range < e.x < x1 + self.pos_range and y0 - self.pos_range < e.y < y1 - self.pos_range:
            print("鼠标在矩形内部.")
            self.move_rect_funcid = self.canvas.bind("<B1-Motion>", self.move_rect)
            # self.canvas.config(cursor="fleur")
                        
        elif not self.rect in self.canvas.find_overlapping(x0 - self.pos_range, y0 - self.pos_range, x0 + self.pos_range, y0 + self.pos_range):
        # else:
            print("bind: <B1-Motion> self.resize_rect")
            self.resize_rect_funcid = self.canvas.bind("<B1-Motion>", self.resize_rect)
    

    def mouseUp(self, e):

        # 检测某个组件是否绑定了指定事件
        if not self.canvas.tag_bind(self.rect, '<Enter>'):
            self.mouse_enter_id = self.canvas.tag_bind(self.rect, "<Enter>", self.mouse_enter)
            self.mouse_restore_id = self.canvas.tag_bind(self.rect, "<Leave>", self.mouse_restore)

        if hasattr(self, "resize_rect_fundic"):
            self.canvas.unbind("<B1-Motion>", self.resize_rect_funcid)
            self.resize_rect_funcid =None

        # 只要不是在矩形内就是外面
        if hasattr(self, "move_rect_funcid"):
            self.canvas.unbind("<B1-Motion>", self.move_rect_funcid)
            self.move_rect_funcid = None
        

    def resize_rect(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        x0, y0, x1, y1 = self.canvas.coords(self.rect)

        # 左上
        if self.left_up:
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            self.canvas.coords(self.rect, x, y, x1, y1)

        # 右下
        elif self.right_down:
            if x > self.w:
                x = self.w
            if y > self.h:
                y = self.h

            self.canvas.coords(self.rect, x0, y0, x, y)


    def move_rect(self, event):

        print(f"{event.x=}, {event.y=}")
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        print(f"鼠标在画布上的坐标：{x=} {y=}")

        # 矩形当前的位置
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        print(f"当前矩形位置：", x0, y0, x1, y1)

        # 矩形本身的大小
        rect_x_move_area = self.w - (x1 - x0)
        rect_y_move_area = self.h - (y1 - y0)

        move_x = x - self.x0
        move_y = y - self.y0

        # 如果已经在画布边界，就不在移动。
        if x0 + move_x <= 0:
            move_x = 0
        elif x0 + move_x >= rect_x_move_area:
            move_x = 0
        
        if y0 + move_y <= 0:
            move_y = 0
        elif y0 + move_y >= rect_y_move_area:
            move_y = 0

        # 这里的 x y 是相对移动的像素。
        self.canvas.move(self.rect, move_x, move_y)

        # 最后需要保存本次鼠标位置，供下次移动事件使用
        self.x0, self.y0 = event.x, event.y


    def loop(self):
        self.root.mainloop()


# 测试，画布跟着窗口大小自动改变
class ResizeCanvas(Canvas_Rectangle):

    def __init__(self):
        super().__init__()

        # 画布一个20像素的矩形看看有多宽
        tmp = self.canvas.create_rectangle(100, 100, 120, 200, width=10, outline='green')

        tmp2 = self.canvas.create_oval(200, 200, 300, 300, width=10, outline='blue')

        self.root.bind("<Configure>", self.resize_canvas)

    
    def resize_canvas(self, e):
        print(f"{__name__=} {e=}")
        self.w = e.width
        self.h = e.height

        # w2 = self.root.winfo_reqheight()
        # h2 = self.root.winfo_reqheight()

        self.canvas.config(width=e.width, height=e.height)
        # self.canvas.config(width=w2, height=h2)


if __name__ == "__main__":
    root = Canvas_Rectangle()
    # root = ResizeCanvas()
    root.loop()
