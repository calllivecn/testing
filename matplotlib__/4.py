#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-1  21:10:55
# https://github.com/calllivecn


import numpy as np
from matplotlib import pyplot as plt



x = np.linspace(-100, 100, 200)

f1="y=(2*x - 5) + (sin(x)*5 + 2)"
y = (2*x - 5) + (np.sin(x)*5 + 2)

f2="y=(2*x - 5) + (sin(x)+1)"
y2 = (2*x-5) * (np.sin(x)+1)

# plt.figure()

fig, ax = plt.subplots()
plt.axis('equal')

# 去掉两个 spine, 把x轴y轴移动到原点
ax.spines.top.set_visible(False)
ax.spines.right.set_visible(False)
ax.spines.bottom.set_position(("data", 0))
ax.spines.left.set_position(("data", 0))


plt.plot(x, y, label=f1)

plt.plot(x, y2, label=f2)

plt.legend()
plt.show()
