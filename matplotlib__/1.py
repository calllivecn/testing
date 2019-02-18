#!/usr/bin/env python3
# coding=utf-8
# date 2019-02-18 17:26:32
# https://github.com/calllivecn

import matplotlib.pyplot as plt
import numpy as np


#fig = plt.figure()
#
#fig.suptitle('No axes on this figure')
#
#fig, ax_lst = plt.subplots(2, 2)
#
#plt.legend()
#plt.show()
#exit(0)

x = np.linspace(0, 2, 100)

plt.figure("1、2、3次函数图像")
plt.plot(x, x, label="y=x")
plt.plot(x, x**2, label="y=x^2")
plt.plot(x, x**3, label="y=x^3")

plt.xlabel('x')
plt.ylabel('y')

plt.legend()

plt.show()
