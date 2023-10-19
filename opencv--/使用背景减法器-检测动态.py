import cv2

from conf import VIDEO as video

# 打开视频文件
cap = cv2.VideoCapture(video)

win1name = 'Original Video'
win2name = 'Dynamic Objects'
cv2.namedWindow(win1name, cv2.WINDOW_NORMAL)
cv2.namedWindow(win2name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(win1name, 800, 600)
cv2.resizeWindow(win2name, 800, 600)

# 创建背景减法器
fgbg = cv2.createBackgroundSubtractorMOG2()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # 应用背景减法器，检测动态物体
    fgmask = fgbg.apply(frame)

    # 通过阈值处理二值化图像
    threshold = 50  # 调整阈值以适应场景
    _, binary_image = cv2.threshold(fgmask, threshold, 255, cv2.THRESH_BINARY)

    # 查找二进制图像中的轮廓
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 绘制边界框
    for contour in contours:
        if cv2.contourArea(contour) > 800:  # 调整面积阈值以过滤小轮廓
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 显示原始帧和检测结果
    cv2.imshow(win1name, frame)
    cv2.imshow(win2name, binary_image)

    if cv2.waitKey(1) & 0xFF == 27:  # 按Esc键退出
        break

cap.release()
cv2.destroyAllWindows()
