# coding=utf-8


import sys
import time

import cv2

from conf import VIDEO as video



def main():
    # cv2.namedWindow("ipcamera", 1)
    # 开启ip摄像头
    # admin是账号，admin是密码
    # 
    # video = "http://zx:zxvideo@192.168.8.170:8080/"  # 此处@后的ipv4 地址需要修改为自己的地址
    # video = "rtsp://admin:zxvideo@192.168.8.170:8554/live"  # 此处@后的ipv4 地址需要修改为自己的地址

    # capture = cv2.VideoCapture(video)
    capture = cv2.VideoCapture(video, cv2.CAP_FFMPEG, [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY ])

    if not capture.isOpened():
        print("Cannot open camera")
        sys.exit(1)


    # 获取视频的WxH
    w_h = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = capture.get(cv2.CAP_PROP_FPS)
    
    """
        fourcc_maps = {'.avi': 'I420',
                       '.m4v': 'mp4v',
                       '.mp4': 'avc1',
                       '.ogv': 'THEO',
                       '.flv': 'FLV1',
    """
    # 保存为文件
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter("output.mp4", fourcc, 20, w_h)

    num = 0
    while True:
        start = time.time()

        success, img = capture.read()
        if success:
            #out.write(img)
            # cv2.imshow("camera", img)
            pass

        # 按键处理，注意，焦点应当在摄像头窗口，不是在终端命令行窗口
        key = cv2.waitKey(1)

        if key == 27:
            # esc键断开连接
            print("esc break...")
            break
        if key == ord(' '):
            if success:
                # 保存一张图像到工作目录
                num += 1
                filename = f"frames_{num}.jpg"
                cv2.imwrite(filename, img)

        if not success:
            break

        #time.sleep(1/20)

        end = time.time()

        print(f"视频大小：{w_h} -- FPS：{fps=} 每帧耗时：{round(end - start, 3)}")


    capture.release()
    #out.release()
    cv2.destroyWindow("camera")


if __name__ == '__main__':
    main()