

import os
import sys
import time
from pathlib import Path
from typing import (
    Union,
)

from conf import VIDEO as video

import cv2


class DynamicDetection:

    def __init__(self, history_fps: int):
        self.fps = history_fps

        # 创建背景减法器
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=round(self.fps))

        # 是否录制的状态
        self.record = False

        # 画面是否变化（是否检测到运动)
        self.change = False

        self.fgmask = None

        self.detecion_interval = 1
        self.start = time.time()

        # 进入录制状态后，连续N秒钟没有变化才停止录制。
        self.stop_record_time = 10

        self.start_record_timestamp = 0
    

    def detecion(self, frame):

        if not self.is_detection():
            return 

        self.change = False

        #应用背景减法器，检测动态物体
        self.fgmask = self.fgbg.apply(frame)
        
        # 通过阈值处理二值化图像
        threshold = 50  # 调整阈值以适应场景
        result, binary_image = cv2.threshold(self.fgmask, threshold, 255, cv2.THRESH_BINARY)

        # 查找二进制图像中的轮廓
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 绘制边界框
        for contour in contours:
            if cv2.contourArea(contour) > 800:  # 调整面积阈值以过滤小轮廓
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
                self.change = True

        """
        这里的动作是：
        1. 如果画面变化，查看是否是录制状态，如果不是录制状态就进入录制状态。
        2. 如果画面没有变化，查看是否是录制状态：
            如果是录制状态，比较录制开始时间戳和当前时间的差，有没有大于 self.stop_record_time 。
                如果大于就停止录制，否则，不操作。
            如果不是录制状态, 不操作。
        """
        if self.change:
            
            if self.record:
                self.start_record_timestamp = time.time()
            else:
                self.record = True
        else:
            if self.record:
                if (time.time() - self.start_record_timestamp) >= self.stop_record_time:
                    self.record = False


        return self.change
    

    def is_detection(self):
        end = time.time()
        if (end - self.start) > self.detecion_interval:
            self.start = end
            return True
        else:
            return False


    def __bool__(self):
        return self.change
    

    def is_record(self):
        return self.record



class VideoFile:

    def __init__(self, fps, w_h):
        """
        out = VideoFile(FPS, (w, h))
        out.write()
        out.write()
        ...
        out.close()
        """

        self.fourcc = cv2.VideoWriter_fourcc(*"avc1")
        
        self.fps = fps
        self.w_h = w_h

        self.out = None

    def generate_filename(self):
        filename = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".mp4"
        self.mp4 = Path(filename)
        if self.mp4.exists():
            os.remove(self.mp4)
    

    def write(self, frame):
        if self.out is None or not self.out.isOpened():
            self.generate_filename()
            self.out = cv2.VideoWriter(str(self.mp4), self.fourcc, self.fps, self.w_h)

        self.out.write(frame)
        

    def close(self):
        if self.out is not None and self.out.isOpened():
            self.out.release()


# 逆时针旋转270度
def rotated(image):
    rotated_image = cv2.transpose(image)
    return cv2.flip(rotated_image, 0)  # 水平翻转

# 摄像头规格超过opencv 默认值后 (W:640, H:480)，也不会更高的参数
# 需要手动设置下。

def set_wxh(cap, w, h):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, 30)

# 打开视频文件
cap = cv2.VideoCapture(0)
if (cap.isOpened()):
    print('视频源打开成功')
    set_wxh(cap, 1280, 720)
    print(f"{cap=}")
else:
    print('视频源打开失败')
    sys.exit(1)

# 获取视频的WxH
w_h = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
src_fps = cap.get(cv2.CAP_PROP_FPS)

print(f"源视频大小：{w_h}, FPS: {src_fps}")

win1name = '源视频'
win2name = '动态检测'
cv2.namedWindow(win1name, cv2.WINDOW_NORMAL)
cv2.namedWindow(win2name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(win1name, 800, 600)
cv2.resizeWindow(win2name, 800, 600)


dd = DynamicDetection(src_fps)

# 保存为文件
# videofile = VideoFile(src_fps, w_h)

start = time.time()

while True:

    ret, frame = cap.read() # frame is img
    if not ret:
        print("cv2.VideoCapture()退出。")
        break

    # frame = rotated(frame)

    dd.detecion(frame)
    
    if dd.is_record():
        msg = "开始录制"
        # videofile.write(frame)
    else:
        msg = "停止录制"
        # videofile.close()


    # 显示原始帧和检测结果
    cv2.imshow(win1name, frame)
    fgmask = None
    if fgmask is not dd.fgmask:
        cv2.imshow(win2name, dd.fgmask)
        fgmask = dd.fgmask

    if cv2.waitKey(1) & 0xFF == 27:  # 按Esc键退出
        print("退出")
        break
    
    
    end = time.time()
    fps = round(1/(end - start))
    print(f"FPS：{fps} -- {msg}  {dd.is_detection()=}", end="")
    print("\r", end="")

    start = end


cap.release()
cv2.destroyAllWindows()
