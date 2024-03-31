#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-17 07:41:49
# author calllivecn <calllivecn@outlook.com>

import cv2

# 打开视频文件
cap = cv2.VideoCapture('video.mp4')

# 获取视频帧率
fps = cap.get(cv2.CAP_PROP_FPS)

# 获取视频总帧数
total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

# 定义输出视频文件名
output_file = 'output.avi'

# 定义输出视频编码格式
fourcc = cv2.VideoWriter_fourcc(*'XVID')

# 定义输出视频对象
out = cv2.VideoWriter(output_file, fourcc, fps, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

# 定义前一帧图像
prev_frame = None

# 定义动态时间段开始和结束帧数
start_frame = None
end_frame = None

# 遍历视频的每一帧
for i in range(int(total_frames)):
    # 读取当前帧图像
    ret, frame = cap.read()

    # 如果读取失败，则退出循环
    if not ret:
        break

    # 如果前一帧图像不为空，则计算当前帧与前一帧的差异值
    if prev_frame is not None:
        diff = cv2.absdiff(frame, prev_frame)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 如果当前帧有动态，则更新动态时间段结束帧数
        if len(contours) > 0:
            end_frame = i

            # 如果动态时间段开始帧数为空，则更新动态时间段开始帧数
            if start_frame is None:
                start_frame = i

    # 更新前一帧图像为当前帧图像
    prev_frame = frame

# 设置视频读取位置为动态时间段开始帧数
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

# 遍历动态时间段内的每一帧，并写入输出视频对象中
for i in range(start_frame, end_frame + 1):
    ret, frame = cap.read()

    # 如果读取失败，则退出循环
    if not ret:
        break

    out.write(frame)

# 释放输入和输出视频对象
cap.release()
out.release()


"""
在上面的代码示例中，我们使用了OpenCV的cv2.absdiff()函数计算当前帧与前一帧之间的差异值，
并使用cv2.threshold()函数将差异值转换为二进制图像。
这里的阈值大小是25，这意味着如果差异值大于25，则将其视为前后帧之间的动态。
"""
