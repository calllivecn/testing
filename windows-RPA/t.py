import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import sys
import os
import time # 导入 time 库用于添加延时

def capture_window_printwindow(hwnd, output_filename="screenshot.png"):
    """
    使用 PrintWindow API 截取指定句柄的窗口画面。
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

    try:
        # 2. 获取窗口的设备上下文 (DC)
        # GetWindowDC 包含非客户区，GetDC(hwnd) 只获取客户区
        # 对于游戏画面，通常需要客户区
        # hdc = win32gui.GetWindowDC(hwnd) # 获取整个窗口 DC
        hdc = win32gui.GetDC(hwnd) # 获取客户区 DC

        # 3. 创建兼容的内存设备上下文 (Memory DC)
        # 注意：创建 DC 需要一个参考 DC，这里使用屏幕 DC 作为参考，或者使用窗口自己的 DC
        # 使用窗口自己的 DC 更保险
        mfcDC = win32ui.CreateDCFromHandle(hdc)
        saveDC = mfcDC.CreateCompatibleDC()

        # 4. 获取窗口尺寸
        # GetClientRect 获取客户区尺寸，相对于窗口左上角 (0,0)
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
             print(f"错误: 获取到的窗口尺寸无效: 宽度 {width}, 高度 {height}")
             return None

        # 5. 创建兼容的位图 (Bitmap)
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)

        # 6. 将位图选入内存 DC
        saveDC.SelectObject(saveBitMap)

        # 7. 将窗口内容绘制到内存 DC
        # 使用 PrintWindow 是关键。参数0通常包含非客户区。
        # 如果只想要客户区，可以尝试 win32con.PW_CLIENTONLY (但对某些应用可能无效)
        print(f"正在调用 PrintWindow 绘制窗口内容 ({width}x{height})...")
        # result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), win32con.PW_CLIENTONLY) # 尝试只截客户区
        result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0) # 通常截取整个窗口，但在内存中绘制

        if result == 0:
            print("警告: PrintWindow 调用返回 0，可能未能成功绘制窗口内容。")
            # 如果 PrintWindow 失败，可能需要检查窗口类型或权限问题。
            # return None # 如果 PrintWindow 失败就返回 None

        # 8. 从位图中获取像素数据
        # 注意：这里 BMP 数据的格式是 BGR，Image.frombuffer 需要指定正确的模式
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)


        # 9. 使用 Pillow 创建图片对象并保存
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


        # 确保输出目录存在（如果文件名包含路径）
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")

        img.save(output_filename)
        print(f"截图成功保存到: '{output_filename}'")

        return output_filename

    except Exception as e:
        print(f"发生错误: {e}")
        return None

    finally:
        # 10. 清理 GDI 资源
        print("正在清理 GDI 资源...")
        if 'saveDC' in locals() and saveDC:
            saveDC.DeleteDC()
        if 'mfcDC' in locals() and mfcDC:
            mfcDC.DeleteDC()
        if 'saveBitMap' in locals() and saveBitMap:
             win32gui.DeleteObject(saveBitMap.GetHandle())
        if 'hdc' in locals() and hdc and hwnd:
             win32gui.ReleaseDC(hwnd, hdc) # 释放窗口 DC
        print("资源清理完成。")


# --- 使用方法示例 ---
if __name__ == "__main__":
    target_hwnd = None
    output_file = "captured_window.png"

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 如果提供了参数，认为是窗口标题
        target_window_title = " ".join(sys.argv[1:])
        print(f"尝试通过窗口标题查找窗口: '{target_window_title}'")
        target_hwnd = win32gui.FindWindow(None, target_window_title)
        if not target_hwnd:
            print(f"错误: 未找到标题为 '{target_window_title}' 的窗口！")
            sys.exit(1)
        print(f"找到窗口句柄: {target_hwnd}")

    else:
        # 如果没有提供参数，进入交互模式，通过焦点选择窗口
        print("--- 交互模式：通过焦点选择窗口 ---")
        print("请在几秒钟内切换到您想要截图的目标窗口...")
        countdown = 5 # 延时 5 秒
        for i in range(countdown, 0, -1):
            print(f"请切换窗口... {i} 秒倒计时...", end='\r')
            time.sleep(1)
        print("\n倒计时结束，正在获取当前焦点窗口...")

        # 获取当前前台窗口句柄
        target_hwnd = win32gui.GetForegroundWindow()

        if not target_hwnd:
            print("错误: 未能获取到前台窗口句柄！")
            sys.exit(1)

        # 尝试获取窗口标题并显示
        try:
            window_text = win32gui.GetWindowText(target_hwnd)
            print(f"获取到窗口句柄: {target_hwnd}, 标题: '{window_text}'")
        except Exception as e:
             print(f"获取到窗口句柄: {target_hwnd}, 但获取标题失败: {e}")


    print("-" * 20)
    captured_file = capture_window_printwindow(target_hwnd, output_file)
    print("-" * 20)

    if captured_file:
        print(f"任务完成，截图文件: {captured_file}")
    else:
        print("截图失败。")
