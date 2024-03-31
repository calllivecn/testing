#!/usr/bin/env python3
# coding=utf-8
# date 2021-08-29 05:08:29
# author calllivecn <calllivecn@outlook.com>

import time

import cv2
import numpy as np
import matplotlib.pyplot as plt


target_png = '/mnt/wind/Games/mc-1.17.1/.minecraft/screenshots/.png'
target_png = '/home/zx/work/mc-hangup/mc-fishing-opencv/images/target_1920x1080.png'
temp_png = '/home/zx/work/mc-hangup/mc-fishing-opencv/images/mc-fishing_1920x1080.png'

target_png = '/home/zx/work/mc-hangup/mc-fishing-opencv/images/target_850x480.png'
temp_png = '/home/zx/work/mc-hangup/mc-fishing-opencv/images/mc-fishing_850x480.png'

scale = 1

# img_plt = plt.imread(target_png)
# img_plt = plt.imread(target_png)#要找的大图
# img_rgb = img_plt
# print("dtype and shape:", img_plt, img_plt.shape)

# img = cv2.cvtColor(np.asanyarray(img_plt), cv2.COLOR_RGBA2BGR)
# print("img shape:", img.shape)

img = cv2.imread(target_png)#要找的大图
# img = cv2.resize(img, (0, 0), fx=0.9, fy=0.5)

print("target shape:", img.shape)

template = cv2.imread(temp_png)#图中的小图
# template = cv2.resize(template, (0, 0), fx=0.9, fy=0.9)
template_size= template.shape[:2]
print("template shape:", template.shape)

#找图 返回最近似的点
def search_returnPoint(img,template,template_size):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #, cv2.CV_8U)
    template_ = cv2.cvtColor(template,cv2.COLOR_BGR2GRAY) #, cv2.CV_8U)

    # 不转换成灰度图, 查找速度会变慢。
    # img_gray, template_ = img, template

    result = cv2.matchTemplate(img_gray, template_, cv2.TM_CCOEFF_NORMED)

    # threshold = 0.1
    # res大于70%
    loc = np.where(result >= 0.8)
    # 使用灰度图像中的坐标对原始RGB图像进行标记
    point = ()
    for pt in zip(*loc[::-1]):
        cv2.rectangle(img, pt, (pt[0] + template_size[1], pt[1] + template_size[0]), (7, 249, 151), 2)
        point = pt
    if point==():
        return None,None,None
    return img,point[0]+ template_size[1] /2,point[1]

start = time.time()
img,x_,y_ = search_returnPoint(img,template,template_size)
end = time.time()

print("time:", end - start)

if img is None:
    print("没找到图片")
else:
    plt_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print("找到图片 位置:"+str(x_)+" " +str(y_))
    plt.figure()
    plt.imshow(plt_img, animated=True)
    plt.show()
