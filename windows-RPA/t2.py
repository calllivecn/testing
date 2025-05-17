import win32gui
import win32ui
import win32con
# import win32api # 如果没有用到 win32api 的其他函数，可以不导入
from PIL import Image
import sys
import os
import time
import ctypes # 导入 ctypes 库
from ctypes import wintypes # 导入用于 Windows 数据类型的 wintypes

# --- 使用 ctypes 定义 PrintWindow 函数 ---
# 加载 user32.dll
user32 = ctypes.WinDLL('user32')

# 定义 PrintWindow 函数的签名
# BOOL PrintWindow(HWND hwnd, HDC hdc, UINT flags);
# HWND, HDC 是 Windows 句柄类型
# UINT 是无符号整型
# BOOL 是布尔型返回值 (非零表示成功)
user32.PrintWindow.argtypes = [
    wintypes.HWND, # 参数 1: 目标窗口句柄
    wintypes.HDC,  # 参数 2: 目标设备上下文句柄
    ctypes.c_uint  # 参数 3: 标志 (例如 0 或 PW_CLIENTONLY)
]
user32.PrintWindow.restype = wintypes.BOOL # 返回值类型

# --- 窗口截图函数 (使用 ctypes 调用 PrintWindow) ---
def capture_window_printwindow_ctypes(hwnd, output_filename="screenshot.png"):
    """
    使用 ctypes 调用 PrintWindow API 截取指定句柄的窗口画面。
    即使窗口被其他窗口遮挡，通常也能成功截取。

    Args:
        hwnd (int): 目标窗口的句柄 (HWND)。
        output_filename (str): 保存截图的文件名 (例如: "my_game_screenshot.png")。

    Returns:
        str: 成功保存的文件名，如果失败则返回 None。
    """
    if not hwnd:
        print("错误: 无效的窗口句柄！")
        return None

    # 尝试获取窗口标题用于打印信息
    try:
        window_text = win32gui.GetWindowText(hwnd)
        print(f"正在处理窗口句柄: {hwnd}, 标题: '{window_text}'")
    except Exception:
         print(f"正在处理窗口句柄: {hwnd}, 获取标题失败。")

    # 获取窗口的设备上下文 (DC) - 使用 pywin32
    # GetDC(hwnd) 获取客户区 DC
    hdc = win32gui.GetDC(hwnd)
    if not hdc:
        print("错误: 获取窗口 DC 失败！")
        return None

    # 创建兼容的内存设备上下文 (Memory DC) - 使用 pywin32
    try:
        mfcDC = win32ui.CreateDCFromHandle(hdc)
        saveDC = mfcDC.CreateCompatibleDC()
    except Exception as e:
        print(f"错误: 创建内存 DC 失败: {e}")
        win32gui.ReleaseDC(hwnd, hdc) # 释放之前获取的 DC
        return None


    # 获取窗口尺寸 - 使用 pywin32
    # GetClientRect 获取客户区尺寸
    try:
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
             print(f"警告: 获取到的窗口客户区尺寸无效: 宽度 {width}, 高度 {height}。可能是最小化或隐藏窗口？")
             # 尝试获取整个窗口尺寸作为备用
             left, top, right, bottom = win32gui.GetWindowRect(hwnd)
             width = right - left
             height = bottom - top
             if width <= 0 or height <= 0:
                 print("错误: 获取整个窗口尺寸也无效。无法继续。")
                 # 清理资源
                 saveDC.DeleteDC()
                 mfcDC.DeleteDC()
                 win32gui.ReleaseDC(hwnd, hdc)
                 return None
             else:
                 print(f"使用整个窗口尺寸: 宽度 {width}, 高度 {height}")
    except Exception as e:
        print(f"错误: 获取窗口尺寸失败: {e}")
        # 清理资源
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None


    # 创建兼容的位图 (Bitmap) - 使用 pywin32
    try:
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    except Exception as e:
         print(f"错误: 创建位图失败: {e}")
         # 清理资源
         saveDC.DeleteDC()
         mfcDC.DeleteDC()
         win32gui.ReleaseDC(hwnd, hdc)
         return None

    # 将位图选入内存 DC - 使用 pywin32
    saveDC.SelectObject(saveBitMap)

    # 将窗口内容绘制到内存 DC - ***使用 ctypes 调用 PrintWindow***
    print(f"正在使用 ctypes 调用 PrintWindow 绘制窗口内容 ({width}x{height})...")
    # PrintWindow 的 flags 参数通常是 0，表示标准绘制；PW_CLIENTONLY (0x00000001) 尝试只绘制客户区
    # result = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), win32con.PW_CLIENTONLY) # 尝试只截客户区
    result = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0) # 通常截取整个窗口，但在内存中绘制

    if result == 0:
        print("警告: PrintWindow 调用返回 0，可能未能成功绘制窗口内容。")
        print("原因可能包括：窗口不支持 PrintWindow, 权限问题, 或窗口状态异常。")
        # 如果 PrintWindow 失败，清理资源并返回 None
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None


    # 从位图中获取像素数据 - 使用 pywin32
    try:
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
    except Exception as e:
        print(f"错误: 获取位图数据失败: {e}")
        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None


    # 使用 Pillow 创建图片对象并保存 - 使用 Pillow
    try:
        # Image.frombuffer 参数: mode, size, data, decoder_name, args
        # size 是 (width, height)
        # data 是 bmpstr
        # mode 'RGB' 适用于大多数情况，但需要指定正确的 raw 解码器
        # 'BGRX' 或 'BGRA' 常见于 Windows Bitmaps
        try:
             # 尝试 BGRA，如果位图有 Alpha 通道
             img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRA', 0, 1)
        except ValueError:
             # 如果没有 Alpha 通道，尝试 BGRX
             img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

    except Exception as e:
        print(f"错误: 创建 Pillow 图片对象失败: {e}")
        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None


    # 确保输出目录存在（如果文件名包含路径）
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        except Exception as e:
            print(f"警告: 创建输出目录失败: {e}. 尝试直接保存。")
            output_dir = None # 清空目录，尝试直接保存

    # 保存图片文件
    try:
        img.save(output_filename)
        print(f"截图成功保存到: '{output_filename}'")
        return output_filename
    except Exception as e:
        print(f"错误: 保存截图文件失败: {e}")
        return None

    finally:
        # 10. 清理 GDI 资源
        print("正在清理 GDI 资源...")
        # 确保在出错时也能安全清理
        # 使用 try-except 块，并检查对象是否存在及是否有相应方法
        try:
            if 'saveDC' in locals() and saveDC and hasattr(saveDC, 'DeleteDC'):
                saveDC.DeleteDC()
        except Exception as e:
             print(f"清理 saveDC 时发生错误: {e}")

        try:
            if 'mfcDC' in locals() and mfcDC and hasattr(mfcDC, 'DeleteDC'):
                mfcDC.DeleteDC()
        except Exception as e:
             print(f"清理 mfcDC 时发生错误: {e}")

        try:
            if 'saveBitMap' in locals() and saveBitMap and hasattr(saveBitMap, 'GetHandle'):
                 win32gui.DeleteObject(saveBitMap.GetHandle())
        except Exception as e:
             print(f"清理 saveBitMap 时发生错误: {e}")

        # 释放窗口 DC，只有在 hdc 和 hwnd 都有效时才释放
        try:
            if 'hdc' in locals() and hdc and hwnd and hasattr(win32gui, 'ReleaseDC'):
                 win32gui.ReleaseDC(hwnd, hdc)
        except Exception as e:
             print(f"释放窗口 DC 时发生错误: {e}")

        print("资源清理完成。")


# --- 使用方法示例 ---
if __name__ == "__main__":
    target_hwnd = None
    output_file = "captured_window_ctypes.png" # 修改默认输出文件名，以区分
    countdown_seconds = 5 # 焦点选择模式的倒计时秒数

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 如果提供了参数，认为是窗口标题
        target_window_title = " ".join(sys.argv[1:])
        print(f"--- 标题查找模式 ---")
        print(f"尝试通过窗口标题查找窗口: '{target_window_title}'...")
        # 查找窗口句柄依然使用 pywin32 的 FindWindow
        target_hwnd = win32gui.FindWindow(None, target_window_title)
        if not target_hwnd:
            print(f"错误: 未找到标题为 '{target_window_title}' 的窗口！请确认标题是否精确匹配。")
            sys.exit(1)
        print(f"成功找到窗口句柄: {target_hwnd}")

    else:
        # 如果没有提供参数，进入交互模式，通过焦点选择窗口
        print(f"--- 交互模式：通过焦点选择窗口 ---")
        print(f"请在 {countdown_seconds} 秒内切换到您想要截图的目标窗口...")

        for i in range(countdown_seconds, 0, -1):
            print(f"请切换窗口... {i} 秒倒计时...", end='\r')
            time.sleep(1)
        print("\n倒计时结束，正在获取当前焦点窗口...")

        # 获取当前前台窗口句柄依然使用 pywin32 的 GetForegroundWindow
        target_hwnd = win32gui.GetForegroundWindow()

        if not target_hwnd:
            print("错误: 未能获取到前台窗口句柄！请确保您在倒计时结束前聚焦了目标窗口。")
            sys.exit(1)

        # 尝试获取窗口标题并显示
        try:
            window_text = win32gui.GetWindowText(target_hwnd)
            print(f"获取到窗口句柄: {target_hwnd}, 标题: '{window_text}'")
        except Exception as e:
             print(f"获取到窗口句柄: {target_hwnd}, 但获取标题失败: {e}")


    print("-" * 20)
    # 调用使用 ctypes 的截图函数
    captured_file = capture_window_printwindow_ctypes(target_hwnd, output_file)
    print("-" * 20)

    if captured_file:
        print(f"截图任务完成，截图文件: {captured_file}")
    else:
        print("截图失败。")
