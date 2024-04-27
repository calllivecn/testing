

import tkinter as tk
from tkinter import (
    ttk,
    filedialog,
)


# 创建 Tk 窗口
root = tk.Tk()

# 创建菜单栏对象
menubar = tk.Menu(root)


# 定义菜单项事件处理函数
def on_new():
    print("New")

def on_open():
    # 让用户选择一个文件
    filename = filedialog.askopenfilename(title="Select a file", initialdir=".", filetypes=[("Text files", "*.txt"), ("所有文件", "*.*")])


    # 打印文件名
    print(f"{type(filename)=}")
    print("Open")

# tearoff: 决定菜单项是否可以从菜单栏中撕下。
# label: 菜单项的文本。
# 创建文件菜单
file_menu = tk.Menu(menubar, tearoff=0)
 

file_menu.add_command(label="New", command=on_new)
file_menu.add_command(label="Open", command=on_open)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# 将菜单添加到菜单栏中
menubar.add_cascade(label="File", menu=file_menu)

# 显示窗口
root.config(menu=menubar)
root.mainloop()