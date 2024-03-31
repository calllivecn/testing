#!/usr/bin/env python3
# coding=utf-8
# date 2021-08-29 05:42:40
# author calllivecn <calllivecn@outlook.com>

import time

import cv2
import numpy as np
import matplotlib.pyplot as plt

# good
import pyscreenshot

# 只能 要 X11 使用。
# from PIL import (
    # ImageGrab,
    # Image,
# )

def test_speed():
    for _ in range(10):
        start = time.time()
        img = pyscreenshot.grab(bbox=(600, 600, 900, 1000))
        np.asanyarray(img)
        # img = pyscreenshot.grab()
        end = time.time()
        print("time:", end - start)

    return img

img  = test_speed()

plt.figure()
plt.imshow(img, animated=True)
plt.show()

