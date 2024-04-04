
import tkinter as tk

import cv2
import numpy as np

import imagepath

# 读取原始图像
# img = cv2.imread('image.jpg')
img = cv2.imread(imagepath.IMG_PATH)

print(img)


factor = 3
# 创建一个空图像，大小为原始图像的两倍
img_放大 = np.zeros((img.shape[0] * factor, img.shape[1] * factor, img.shape[2]), dtype=img.dtype)

# 遍历原始图像的每个像素
for i in range(img.shape[0]):
    for j in range(img.shape[1]):
        # 将像素值复制到放大后的图像中
        img_放大[i * factor, j * factor] = img[i, j]
        img_放大[i * factor + 1, j * factor] = img[i, j]
        img_放大[i * factor, j * factor + 1] = img[i, j]
        img_放大[i * factor + 1, j * factor + 1] = img[i, j]

# 显示放大后的图像


# 将图像转换为 PNG 格式
bool_, img_encoded = cv2.imencode('.png', img_放大)
print("成功了吗？", bool_)


# 创建一个 Tk 窗口
root = tk.Tk()

# 创建一个 PhotoImage 对象 # 将图像数据转换为字节数组
img_tk = tk.PhotoImage(data=img_encoded.tobytes())

# 将 PhotoImage 对象显示在窗口中
label = tk.Label(root, image=img_tk)
label.pack()

# 运行 Tk 窗口
root.mainloop()
