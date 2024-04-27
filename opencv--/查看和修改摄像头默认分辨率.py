

import sys

import cv2
 
videoCaputer = cv2.VideoCapture(0)
if (videoCaputer.isOpened()):
    print('视频源打开成功')
    print(f"{videoCaputer=}")
else:
    print('视频源打开失败')
    sys.exit(1)

# xiaomi 上不行
# H_max = videoCaputer.get(cv2.CAP_PROP_FRAME_COUNT)
# W_max = videoCaputer.get(cv2.CAP_PROP_GIGA_FRAME_HEIGH_MAX)
# print(f"{H_max=} {W_max=}")
 
size = (int(videoCaputer.get(cv2.CAP_PROP_FRAME_WIDTH)), int(videoCaputer.get(cv2.CAP_PROP_FRAME_HEIGHT)))
print(f"默认分辨率大小：{size}")
fps = videoCaputer.get(cv2.CAP_PROP_FPS)
print(f"默认fps：{fps}")


 
# 只要set下，貌似size就发生了变化
videoCaputer.set(cv2.CAP_PROP_FRAME_WIDTH, 20000)
videoCaputer.set(cv2.CAP_PROP_FRAME_HEIGHT, 20000)

fps = videoCaputer.get(cv2.CAP_PROP_FPS)
 
size = (int(videoCaputer.get(cv2.CAP_PROP_FRAME_WIDTH)), int(videoCaputer.get(cv2.CAP_PROP_FRAME_HEIGHT)))

_,frame = videoCaputer.read()

print(f"设置之后的分辨率大小：{size} {frame.shape=}") # 正确结果（1024,1280, 3）
print(f"设置之后fps：{fps}")


videoCaputer.release()