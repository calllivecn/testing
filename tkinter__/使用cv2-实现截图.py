
import tkinter as tk

import cv2

import imagepath

# 读取原始图像
# img = cv2.imread('image.jpg')
img = cv2.imread(imagepath.IMG_PATH)


def image_screenshot(image, x, y, w, h):
  """
  图片截图函数

  Args:
    image: 输入图像
    x: 截图起始点的横坐标
    y: 截图起始点的纵坐标
    w: 截图的宽度
    h: 截图的高度

  Returns:
    截图后的图像
  """

  # 从输入图像中截取指定区域的图像
  screenshot = image[y:y+h, x:x+w]

  # 返回截图后的图像
  return screenshot


new_img = image_screenshot(img, 100, 100, 300, 300)



# 将图像转换为 PNG 格式
bool_, img_encoded = cv2.imencode('.png', new_img)
print("成功了吗？", bool_)

# 创建一个 Tk 窗口
root = tk.Tk()

img_tk = tk.PhotoImage(data=img_encoded.tobytes())

label = tk.Label(root, image=img_tk)
label.pack()

cv2.imwrite("/tmp/out-tset.png", new_img)

# 运行 Tk 窗口
root.mainloop()
