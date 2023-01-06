# coding=utf-8


import sys
import time

import cv2


if __name__ == '__main__':

    cv2.namedWindow("桌面", 1)
    # 开启ip摄像头
    # admin是账号，admin是密码
    # 
    capture = cv2.VideoCapture(0)

    if not capture.isOpened():
        print("Cannot open camera")
        sys.exit(1)

    # 获取视频的WxH
    w_h = (int(capture.get(3)), int(capture.get(4)))
    print(w_h)
    
    # 保存为文件
    fourcc = cv2.VideoWriter_fourcc(*"x265")
    out = cv2.VideoWriter("output.mp4", fourcc, 20, w_h)

    num = 0
    while True:
        success, img = capture.read()
        out.write(img)
        cv2.imshow("camera", img)

        # 按键处理，注意，焦点应当在摄像头窗口，不是在终端命令行窗口
        key = cv2.waitKey(1)

        if key == 27:
            # esc键断开连接
            print("esc break...")
            break
        if key == ord(' '):
            # 保存一张图像到工作目录
            num = num + 1
            filename = f"frames_{num}.jpg"
            cv2.imwrite(filename, img)

        if not success:
            break

        # time.sleep(1/20)

    capture.release()
    out.release()
    cv2.destroyWindow("camera")
