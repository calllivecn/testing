
import cv2
import tkinter as tk

import imagepath

# 读取原始图像
# img = cv2.imread('image.jpg')
img = cv2.imread(imagepath.IMG_PATH)

# 将图像转换为 PNG 格式
bool_, img_encoded = cv2.imencode('.png', img)
print("成功了吗？", bool_)

# 将图像数据转换为字节数组
img_bytes = img_encoded.tobytes()

# 创建一个 Tk 窗口
root = tk.Tk()

# 创建一个 PhotoImage 对象
img_tk = tk.PhotoImage(data=img_bytes)

# 将 PhotoImage 对象显示在窗口中
label = tk.Label(root, image=img_tk)
label.pack()

# 运行 Tk 窗口
root.mainloop()
