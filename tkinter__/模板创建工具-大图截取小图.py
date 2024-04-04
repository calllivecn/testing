
"""
Tkinter 原生只支持 PNG 和 GIF 格式的图片。
"""

"""
canvas.xview() 和 canvas.yview() 方法用于设置和获取画布的水平和垂直滚动视图。

xview() 方法

xview() 方法的第一个参数可以是以下值之一：

"moveto"：将滚动视图移动到指定的水平位置。
"scroll"：将滚动视图向左或向右滚动指定的单位。
"fraction"：将滚动视图移动到指定的水平比例。
xview() 方法的第二个参数是水平位置、滚动单位或水平比例。


# 将滚动视图移动到水平位置 100
canvas.xview("moveto", 100)

# 将滚动视图向右滚动 10 个单位
canvas.xview("scroll", 10, "units")

# 将滚动视图移动到水平比例 0.5
canvas.xview("fraction", 0.5)

yview() 一样。

"""


import tkinter as tk
from tkinter import (
    ttk,
    filedialog,
)
from pathlib import Path

import cv2
# import numpy as np

HELP_INFO="""\
1. ↑↓←→方向键移动截图框。
2. shift+方向键，扩大截图框。
3. Alt+方向键，缩小截图框。
4. w, s, a, d键是移动窗口在图片上的位置。(当前图片比窗口大时)
5. z键在快速和慢速之间来回切换,截图框的速度。

"""

class PhotoScreenshot:

    def __init__(self):

        # 乘放系数
        self.factor = 1

        self.root = tk.Tk()
        self.root.title("截图模板提取工具")

        self.root.geometry("1920x1080")

        self.frame_canvas = tk.Frame(master=self.root)
        self.frame_canvas.pack()


        self.on_key_press()
    

        self.image_filename = ""
        self.image_dirname = "."
        self.output_dirname = "."
        self.__menu()

        self.canvas = None


        self._help_info: bool = False


    def __help_info(self):
        # 这个点几次就会执行几次，需要打个标判断一下。
        if self._help_info:
            pass
        else:
            help_window = tk.Toplevel(self.root)
            help_window.title("使用说明")
            self._help_info = True

            def func_tmp():
                self._help_info = False
                help_window.destroy()

            help_window.protocol("WM_DELETE_WINDOW", func_tmp)

            label_text = ttk.Label(help_window, text=HELP_INFO)
            label_text.pack()


    def canvas_open_photo(self):

        if self.canvas is not None:
            self.canvas.destroy()

        self.cv2_img = cv2.imread(self.image_filename)
        bool_, img_encoded = cv2.imencode('.png', self.cv2_img)
        if not bool_:
            raise ValueError("""cv2.imencode(".png") 转换图片格式失败...""")
        

        # 只支持 png gif格式
        # self.photo_image = tk.PhotoImage(file=imagepath.IMG_PATH)
        # self.photo_image = tk.PhotoImage(file=self.image_filename)
        self.photo_image = tk.PhotoImage(data=img_encoded.tobytes())

        self.image_width = self.photo_image.width()
        self.image_height = self.photo_image.height()

        print(f"图片大小: {self.image_width}x{self.image_height}")

        # 设置画布大小？
        # 创建 Canvas 控件
        # canvas = tk.Canvas(master=frame_canvas) # 这样不行，只有画布的默认大小
        self.canvas = tk.Canvas(master=self.frame_canvas, width=self.photo_image.width(), height=self.photo_image.height())

        # 使用小的画布，查看大的图片
        self.canvas.config(scrollregion=(0, 0, self.image_width, self.image_height))

        self.canvas.config(border=1)

        # 绘制图片
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

        # 创建截图矩形
        self.__rect()

        # label1 = tk.Label(root, image=photo_image)
        # label1.pack()

        # 显示窗口
        self.canvas.pack()



    def __menu(self):
        self._menu = tk.Menu(self.root)

        file_menu = tk.Menu(self._menu, tearoff=0)
        self._menu.add_cascade(label="文件", menu=file_menu)

        file_menu.add_command(label="打开图片", command=self.__open_photo)

        file_menu.add_command(label="保存截图", command=self.__save_screenshot)
        file_menu.add_separator()
        file_menu.add_command(label="帮助", command=self.__help_info)

        self.root.config(menu=self._menu)
    

    def __open_photo(self):
        self.image_filename = filedialog.askopenfilename(title="选择图片", initialdir=self.image_dirname, filetypes=[("png", "*.png"), ("所有文件", "*.*")])

        if self.image_filename == "":
            return

        
        self.image_dirname = Path(self.image_filename).parent
        
        self.canvas_open_photo()
    

    def __save_screenshot(self):
        self.output_filename = filedialog.asksaveasfilename(title="保存文件名", initialdir=self.output_dirname, filetypes=[("png", "*.png")])

        if self.output_filename == "":
            print("没有写入文件名")
            return
        else:
            print("有了", self.output_filename)
            self.output_dirname = Path(self.output_filename).parent

            # x0, y0, x1, y1: 是 float 类型
            x0, y0, x1, y1 = self.canvas.coords(self.rect)
            screenshot_img = self.cv2_img[int(y0):int(y1), int(x0):int(x1)]

            cv2.imwrite(self.output_filename, screenshot_img)


    def on_key_press(self):

        self.step = 10
        self.root.bind("<z>", self.__swap_step)

        print("有绑定上？")

        # 移动截图框
        self.root.bind("<Up>", lambda e :self.__canvas_rect_move(self.step, "Up"))
        self.root.bind("<Down>", lambda e :self.__canvas_rect_move(self.step, "Down"))
        self.root.bind("<Left>", lambda e :self.__canvas_rect_move(self.step, "Left"))
        self.root.bind("<Right>", lambda e :self.__canvas_rect_move(self.step, "Right"))

        # 移动截图框大小, 扩大
        self.root.bind("<Shift-Up>", lambda e :self.__canvas_rect_expand(self.step, "Up"))
        self.root.bind("<Shift-Down>", lambda e :self.__canvas_rect_expand(self.step, "Down"))
        self.root.bind("<Shift-Left>", lambda e :self.__canvas_rect_expand(self.step, "Left"))
        self.root.bind("<Shift-Right>", lambda e :self.__canvas_rect_expand(self.step, "Right"))
        # 移动截图框大小, 缩小
        self.root.bind("<Alt-Up>", lambda e :self.__canvas_rect_reduce(self.step, "Up"))
        self.root.bind("<Alt-Down>", lambda e :self.__canvas_rect_reduce(self.step, "Down"))
        self.root.bind("<Alt-Left>", lambda e :self.__canvas_rect_reduce(self.step, "Left"))
        self.root.bind("<Alt-Right>", lambda e :self.__canvas_rect_reduce(self.step, "Right"))


        # 移动画布视窗
        self.root.bind("<w>", lambda e :self.__canvas_view_move(e, "Up"))
        self.root.bind("<s>", lambda e :self.__canvas_view_move(e, "Down"))
        self.root.bind("<a>", lambda e :self.__canvas_view_move(e, "Left"))
        self.root.bind("<d>", lambda e :self.__canvas_view_move(e, "Right"))

        # 后期，上图片缩放
        # self.canvas.bind("<MouseWheel>", self.__photo_scale)
    

    def __swap_step(self, e):
        if self.step == 1:
            self.step = 10
        elif self.step == 10:
            self.step = 1


    def __rect(self):
        # 画线宽度
        self.outline_width = 1
        self.outline_color = "red"

        # 截图矩形的相对位置, 左上角位置，右下角位置
        self.rect_x0 = 0
        self.rect_y0 = 0
        self.rect_x1 = self.image_width // 3
        self.rect_y1 = self.image_height // 3

        # 这里坐标是矩形的左上角和右下角坐标
        self.rect = self.canvas.create_rectangle(self.rect_x0, self.rect_y0, self.rect_x1, self.rect_y1, width=self.outline_width, outline=self.outline_color)


    def __canvas_rect_move(self, step: int, direction: str):

        # 鼠标在画布上的坐标
        # x, y = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)

        # 矩开当前相对画布的位置
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        # print("x0, y0, x1, y1:", x0, y0, x1, y1)

        # 矩形本身的大小, 这里是实现，小矩形不能跑到画布外面的问题
        rect_x_move_area = (x1 - x0)
        rect_y_move_area = (y1 - y0)


        move_x = 0
        move_y = 0

        if direction == "Up":
            move_y -= step

        elif direction == "Down":
            move_y += step

        elif direction == "Left":
            move_x -= step

        elif direction == "Right":
            move_x += step


        # 如果已经在画布边界，就不在移动。
        if x0 + move_x <= 0:
            move_x = 0
        elif x0 + move_x + rect_x_move_area > self.image_width:
            move_x = 0
        
        if y0 + move_y <= 0:
            move_y = 0
        elif y0 + move_y + rect_y_move_area > self.image_height:
            move_y = 0

        # print(f"{move_x=} {move_y=}")
        # 这里的 x y 是相对移动的像素。
        self.canvas.move(self.rect, move_x, move_y)


    def __canvas_rect_expand(self, step: int, direction: str):
        # 扩大

        x0, y0, x1, y1 = self.canvas.coords(self.rect)

        if direction == "Up":
            if y0 - step >= 0:
                self.canvas.coords(self.rect, x0, y0 - step, x1, y1)

        elif direction == "Down":
            if y1 + step <= self.image_height:
                self.canvas.coords(self.rect, x0, y0, x1, y1 + step)

        elif direction == "Left":
            if x0 - step >= 0:
                self.canvas.coords(self.rect, x0 - step, y0, x1, y1)

        elif direction == "Right":
            if x1 + step <= self.image_width:
                self.canvas.coords(self.rect, x0, y0, x1 + step, y1)


    def __canvas_rect_reduce(self, step: int, direction: str):
        # 缩小

        x0, y0, x1, y1 = self.canvas.coords(self.rect)

        if direction == "Up":
            if y1 - step >= 0:
                self.canvas.coords(self.rect, x0, y0, x1, y1 - step)

        elif direction == "Down":
            if y0 + step <= self.image_height:
                self.canvas.coords(self.rect, x0, y0 + step, x1, y1)

        elif direction == "Left":
            if x1 - step >= 0:
                self.canvas.coords(self.rect, x0, y0, x1 - step, y1)

        elif direction == "Right":
            if x0 + step <= self.image_width:
                self.canvas.coords(self.rect, x0 + step, y0, x1, y1)



    def __canvas_view_move(self, e, direction: str):

        if direction == "Up":
            self.canvas.yview("scroll", -1, "units")

        elif direction == "Down":
            self.canvas.yview("scroll", 1, "units")

        elif direction == "Left":
            self.canvas.xview("scroll", -1, "units")

        elif direction == "Right":
            self.canvas.xview("scroll", 1, "units")

    
    def __photo_scale(self, e):
        # 获取鼠标滚轮滚动的方向
        delta = e.delta

        # 向上滚动
        if delta > 0:
            # 缩小
            if self.factor >= 1:
                self.factor -= 1
                self.photo_image2 = self.photo_image.subsample(self.factor)

                self.canvas.itemconfig(self.canvas, image=self.photo_image2)
                self.image_width = self.photo_image2.width()
                self.image_height = self.photo_image2.height()
                print("图片大小:", self.photo_image2.width(), self.photo_image2.height())

        # 向下滚动
        else:
            # 放大
            self.factor += 1
            self.photo_image2 = self.photo_image.zoom(self.factor)

            self.canvas.itemconfig(self.canvas, image=self.photo_image2)
            self.image_width = self.photo_image2.width()
            self.image_height = self.photo_image2.height()
            print("图片大小:", self.photo_image2.width(), self.photo_image2.height())


    def mainloop(self):
        self.root.mainloop()



def test():
    photo = PhotoScreenshot()
    photo.mainloop()
    

if __name__ == "__main__":
    test()

