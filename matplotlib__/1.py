#!/usr/bin/env python3
# coding=utf-8
# date 2019-02-18 17:26:32
# https://github.com/calllivecn


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


#fig = plt.figure()
#
#fig.suptitle('No axes on this figure')
#
#fig, ax_lst = plt.subplots(2, 2)
#
#plt.legend()
#plt.show()
#exit(0)

# x = np.linspace(0, 2, 100)
# x = np.linspace(-100, 100, 1000, dtype=np.float32)
x = np.linspace(-100, 100, 1000)

# plt.figure("1、2、3次函数图像")
fig, ax = plt.subplots()
plt.axis('equal')
print(type(ax), ax)


# 去掉两个 spine, 把x轴y轴移动到原点
ax.spines.top.set_visible(False)
ax.spines.right.set_visible(False)
print(type(ax.spines), ax.spines)
ax.spines.bottom.set_position(("data", 0))
ax.spines.left.set_position(("data", 0))


# 画 x,y 的平行线
# plt.axhline(0, color="black")
# plt.axvline(0, color="black")

ax2 = plt.subplot()
plt.plot(x, 2*x+5, ":", label="y=2x + 5")
plt.plot(x, x, label="y=x")

x3 = np.linspace(-6, 6, 100)
plt.plot(x3, x3**2, label="y=x^2")
plt.plot(x3, x3**3, label="y=x^3")
plt.plot(x, np.sin(x/2) * 20, label="sin(x/2)")

plt.plot(x3, x3*2 - 20*x3 - 3, label="y=x^2 - 20x - 3")

# plt.plot(x, x*np.sqrt(1 - 2**2), label="y=x*sqrt(1-2^2)")
# plt.plot(x, x*np.exp(1), label="y=x*e")

plt.plot(x, 1/x, label="y=1/x")

r_a = np.pi/180*30

xy2 = np.array([x, 1/x])

R = np.array([
    [np.cos(r_a), -np.sin(r_a)],
    [np.sin(r_a), np.cos(r_a)]
])

x2_y2 = R.dot(xy2)

plt.plot(x2_y2[0], x2_y2[1], label="rotation(30)")

# 这样生成的圆，边界是断开的。
# y = np.sqrt(50**2 - (x**2))
# y2 = np.concatenate((y, -y))
# plt.plot(np.concatenate((x, x)), y2, label="x^2 + y^2 = 50^2")


# 这样生成的圆完整
R = 70
a = np.linspace(0, np.pi*2, 1000)
x2 = np.cos(a) * R + 20
y2 = np.sin(a) * R + 20
plt.plot(x2, y2, label="Circle:(20, 20), R:70")

# 使用 plt 自带的也可以生成完整圆
c = Circle((20, 20), 20, fill=False)
c_ = ax.add_patch(c)

plt.legend()

plt.show()
