#!/usr/bin/env python3
# coding=utf-8
# date 2019-02-18 18:05:45
# https://github.com/calllivecn


import matplotlib.pyplot as plt
import numpy as np


x = np.arange(0, 20, 0.1)

y = np.sin(x)

fig, ax = plt.subplots()

ax.plot(x, y)

#plt.figure("sin函数图像")

plt.show()
