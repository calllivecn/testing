
import sys
import time

import cv2
import numpy as np

img_name = sys.argv[1]

# 强制检查 OpenCL 是否可用
if not cv2.ocl.haveOpenCL():
    print("OpenCL 硬件加速不可用")
    exit()

cv2.ocl.setUseOpenCL(True)
print(f"当前 OpenCL 设备: {cv2.ocl.Device.getDefault().name()}")

# 读取图像
#img = cv2.imread("test.jpg")
img = cv2.imread(img_name)

# 检查图像是否成功加载
if img is None:
    print(f"无法读取图像: {img_name}")
    exit()

# 将 numpy 数组转换为 UMat (Universal Mat)
# 这一步会将数据上传到 GPU 显存
img_gpu = cv2.UMat(img) # 这样是能正常执行的。

# 后续的所有操作都会在 GPU 上执行
# 注释：OpenCV 会根据硬件情况自动选择 OpenCL 内核
start = time.time()
processed_gpu = cv2.cvtColor(img_gpu, cv2.COLOR_BGR2GRAY)
processed_gpu = cv2.GaussianBlur(processed_gpu, (15, 15), 0)
processed_gpu = cv2.Canny(processed_gpu, 50, 150)
end = time.time()

# 将结果从 GPU 下载回 CPU (numpy 格式)
result = processed_gpu.get()

print(f"T-API (OpenCL) 处理耗时: {(end - start) * 1000:.2f} ms")
