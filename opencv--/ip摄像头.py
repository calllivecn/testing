


# coding=utf-8
import cv2
import time


if __name__ == '__main__':

    cv2.namedWindow("camera", 1)
    # 开启ip摄像头
    # admin是账号，admin是密码
    # 
    video = "http://admin:zxvideo@192.168.8.170:8081/"  # 此处@后的ipv4 地址需要修改为自己的地址
    capture = cv2.VideoCapture(video)

    num = 0
    while True:
        success, img = capture.read()
        cv2.imshow("camera", img)

        # 按键处理，注意，焦点应当在摄像头窗口，不是在终端命令行窗口
        key = cv2.waitKey(10)

        if key == 27:
            # esc键断开连接
            print("esc break...")
            break
        if key == ord(' '):
            # 保存一张图像到工作目录
            num = num + 1
            filename = "frames_%s.jpg" % num
            cv2.imwrite(filename, img)
        
        # time.sleep(1/20)

    capture.release()
    cv2.destroyWindow("camera")
