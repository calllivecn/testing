#!/usr/bin/env python3
# coding=utf-8
# date 2021-08-29 07:04:26
# author calllivecn <c-all@qq.com>


from time import sleep

import tkinter as tk



# 创建tkinter主窗口
class Win:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("主窗口")

        # 指定主窗口位置与大小
        self.root.geometry("200x80+200+200")

        # 不允许改变窗口大小
        # root.resizable(False, False)


    def addEvent(self, func):
        # 上个按钮
        btn1 = tk.Button(self.root, text="开始")
        btn1.bind("<Button-1>", func)
        btn1.pack()
    
    def mainloop(self):
        self.root.mainloop()


# 创建顶级组件容器
class Monitor:

    def __init__(self, win):
        self.root = win
        self.top = tk.Toplevel(win)

        self.screen_w = win.winfo_screenwidth()
        self.screen_h = win.winfo_screenheight()
        print("screen:", self.screen_w, self.screen_h)

        self.top.geometry("200x200+400+300")

        self.top.minsize(50, 100)

        self.top.overrideredirect(True)
        
        self.top.attributes('-alpha', 0.0)
        self.top.attributes("-topmost", True) 

        # label = tkinter.Label(top, bg="#f21312")
        # label.pack(fill=tkinter.BOTH, expand="y")

        canvas = tk.Label(self.top, bg="#1122cc", borderwidth=5)
        canvas.pack(fill="both", expand="yes")
        canvas.bind("<Button-1>", self.mouseDown)
        canvas.bind("<B1-Motion>", self.Resize)

        canvas2 = tk.Label(canvas, bg="#ff2233", borderwidth=5)
        canvas2.pack(fill="both", expand="yes", padx=5, pady=5)
        canvas2.bind("<Button-1>", self.mouseDown)
        canvas2.bind("<B1-Motion>", self.moveWin)

        self.show = True
    
    def mouseDown(self, event):
        self.w_x = event.x
        self.w_y = event.y

        self.pos_x = self.top.winfo_x() - event.x
        self.pos_y = self.top.winfo_y() - event.y
        print("mouseDown:", event, "pos_x, pos_y:", self.pos_x, self.pos_y)


    
    def moveWin(self, event):
        # print("move:", event)
        x = self.top.winfo_x() + (event.x - self.w_x)
        y = self.top.winfo_y() + (event.y - self.w_y)

        # print("x y:", f"+{x}+{y}")
        self.top.geometry(f"+{x}+{y}")
        # self.top.update()

    def Resize(self, event):
        self.top.geometry(f"{event.x}x{event.y}")
    
    def hideen(self, event):
        # 要输出 bbox=
        if self.show:
            self.show = False
            self.top.withdraw()
        else:
            self.show = True
            self.top.deiconify()


root = Win()

t = Monitor(root.root)

root.addEvent(t.hideen)

root.mainloop()
