

import cv2
import numpy as np

from conf import VIDEO as video

# 逆时针旋转270度
def rotated(image):
    rotated_image = cv2.transpose(image)
    return cv2.flip(rotated_image, 0)  # 水平翻转


# camera = cv2.VideoCapture(0) , # 读取机器上第一个摄像头
camera = cv2.VideoCapture(video)


if (camera.isOpened()):
    print('视频源打开成功')
else:
    print('视频源打开失败')

# 设置窗口，大小可调。
cv2.namedWindow('win1', cv2.WINDOW_NORMAL)
cv2.namedWindow('win2', cv2.WINDOW_NORMAL)
cv2.resizeWindow('win1', 800, 600)
cv2.resizeWindow('win2', 800, 600)

size = (int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)), int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))
print(f"w x h: {size}")

es = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
kernel = np.ones((5, 5), np.uint8)
background = None

while True:

    grabbed, frame_lwpCV = camera.read()

    if not grabbed:
        print("结束")
        break
    
    frame_lwpCV = rotated(frame_lwpCV)

    gray_lwpCV = cv2.cvtColor(frame_lwpCV, cv2.COLOR_BGR2GRAY)
    gray_lwpCV = cv2.GaussianBlur(gray_lwpCV, (5, 5), 0)

    if background is None:
        background = gray_lwpCV
        continue

    diff = cv2.absdiff(background, gray_lwpCV)
    # 高斯滤波后再采用Otsu阈值
    # blur = cv2.GaussianBlur(diff,(5,5),0)
    # ret3,th3 = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # 二分阈值
    threshlod = 25
    ret, diff = cv2.threshold(diff, threshlod, 255, cv2.THRESH_BINARY)

    diff = cv2.dilate(diff, es, iterations=1)
    # diff = cv2.dilate(diff, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    areas = []
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if area > 40000:
            areas.append(area)
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame_lwpCV, (x, y), (x+w, y+h), (0, 255, 0), 2)

    print(f"前10个轮廓面积：{areas[:10]}")

    cv2.imshow('win1', frame_lwpCV)
    cv2.imshow('win2', diff)

    key = cv2.waitKey(1) & 0xFF
    # if key == ord('q'):
    if key == 27: # ESC
        break

camera.release()
cv2.destroyAllWindows()
