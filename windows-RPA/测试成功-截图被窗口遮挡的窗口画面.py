"""
测试成功。
pip install pywin32 pillow
"""

import time
import ctypes
import win32gui
import win32ui
import win32con
from PIL import Image

def capture_window(hwnd: int, include_border: bool = True) -> Image.Image:
    """
    使用 PrintWindow + DWM 完整截图指定窗口（包括被遮挡或无焦点）。
    hwnd: 窗口句柄。
    include_border: 包含边框和非客户区（Windows 8+）。
    """
    # 获取窗口尺寸
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    print(f"当前窗口，客户区大小：{width}x{height}")

    # 获取窗口 DC，使用 GetDCEx 支持更多场景
    hwnd_dc = win32gui.GetDC(hwnd)
        #win32con.DCX_WINDOW | win32con.DCX_CACHE | win32con.DCX_CLIPSIBLINGS)
    if not hwnd_dc:
        raise RuntimeError("无法获取窗口 DC")

    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    # 创建兼容位图并选入 DC
    save_bmp = win32ui.CreateBitmap()
    save_bmp.CreateCompatibleBitmap(mfc_dc, width, height)
    old_obj = save_dc.SelectObject(save_bmp)

    # 使用 PRINTWINDOW_FULLCONTENT 标志以调用 DWM 绘制完整内容
    PW_RENDERFULLCONTENT = 0x00000002
    flags = PW_RENDERFULLCONTENT if include_border else 0
    res = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), flags)

    # 恢复 GDI 对象
    save_dc.SelectObject(old_obj)

    # 清理 DC
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    if res != 1:
        # 删除位图
        win32gui.DeleteObject(save_bmp.GetHandle())
        raise RuntimeError(f"PrintWindow 截图失败，返回码: {res}")

    # 获取位图数据并销毁对象
    bmp_info = save_bmp.GetInfo()
    bmp_str = save_bmp.GetBitmapBits(True)
    win32gui.DeleteObject(save_bmp.GetHandle())

    # 转换为 PIL.Image
    img = Image.frombuffer(
        'RGB',
        (bmp_info['bmWidth'], bmp_info['bmHeight']),
        bmp_str, 'raw', 'BGRX', 0, 1
    )
    return img

if __name__ == "__main__":
    # 交互式焦点选择
    countdown = 5
    print("--- 交互模式：请在倒计时结束前切换目标窗口 ---")
    for i in range(countdown, 0, -1):
        print(f"{i} 秒后截图...", end='\r')
        time.sleep(1)
        
    print("\n获取前台窗口句柄...")

    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("无法获取前台窗口句柄，请确保窗口已激活。")
    print(f"已选择窗口: {win32gui.GetWindowText(hwnd)}")

    print(f"3秒后开始截图")
    time.sleep(3)

    # 执行截图
    img = capture_window(hwnd, include_border=True)
    save_path = "window_capture.png"
    img.save(save_path)
    print(f"截图已保存: {save_path}")

