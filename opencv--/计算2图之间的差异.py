
import sys
import time

import cv2


from conf import VIDEO as video

# capture = cv2.VideoCapture(video)
capture = cv2.VideoCapture(video, cv2.CAP_FFMPEG, [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY ])

if not capture.isOpened():
    print("Cannot open camera")
    sys.exit(1)

background = None

while True:
    success, img = capture.read()
    if not success:
        print("读取图像失败")
        sys.exit(1)
    
    if background is None:
        background = img
        continue

    gray = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)

    # 高斯模糊去除噪声。
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # 计算两个图像之间的差异
    diff = cv2.absdiff(background, img)
    ret, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 如果当前帧有动态，则更新动态时间段结束帧数
    if len(contours) > 0:
        print("有差异。")
    
        # 标记后的图
        img3 = img.copy()
        cv2.drawContours(img3, contours, -1, (0, 255, 0), 2)
        # 显示结果
        cv2.imshow('src', img)
        cv2.imshow("threshold", thresh)
        cv2.imshow('mark after', img3)
    

    background = img


    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break



# 清理+退出
capture.release()

cv2.destroyAllWindows()

