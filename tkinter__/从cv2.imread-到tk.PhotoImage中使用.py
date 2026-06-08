
import sys
import tkinter as tk

import cv2

# 读取原始图像
img = cv2.imread(sys.argv[1])

# 将图像转换为 PNG 格式
bool_, img_encoded = cv2.imencode('.png', img)
print("成功了吗？", bool_)

# 创建一个 Tk 窗口
root = tk.Tk()

img_tk = tk.PhotoImage(data=img_encoded.tobytes())

label = tk.Label(root, image=img_tk)
label.pack()

# 运行 Tk 窗口
root.mainloop()
