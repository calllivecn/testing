#!/usr/bin/env python3
# coding=utf-8
# date 2019-02-18 18:05:45
# https://github.com/calllivecn


import numpy as np
import matplotlib.pyplot as plt


# 这节做旋转函数图像

# x = np.arange(0, 20, 0.1)

x = np.linspace(-100, 100, 1000)

y = np.sin(x/5) * 20

fig, ax = plt.subplots()
plt.axis('equal')

# 去掉两个 spine, 把x轴y轴移动到原点
ax.spines.top.set_visible(False)
ax.spines.right.set_visible(False)
ax.spines.bottom.set_position(("data", 0))
ax.spines.left.set_position(("data", 0))


# 原图像
ax.plot(x, y, label="y=sin(x/5)*20")

# 做旋转
x2 = x * np.cos(np.pi/4) - y * np.sin(np.pi/4)
y2 = x * np.sin(np.pi/4) + y * np.cos(np.pi/4)  + 30
ax.plot(x2, y2, label="y=(sin(x/5)*20)*cos(pi/4)")


# 做旋转 写成矩阵形式
Asin = np.array([x, y])
# rotation angle 
r_a = np.pi/4
R = np.array([
    [np.cos(r_a), -np.sin(r_a)],
    [np.cos(r_a), np.sin(r_a)]
])
result = R.dot(Asin)
plt.plot(result[0] + 30, result[1])


plt.show()
