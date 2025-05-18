import win32gui
import win32api
import win32con
import time

# 1. 获取目标窗口句柄
# 通过窗口类名和/或窗口标题来查找
# 'Notepad' 是记事本的窗口类名，None 表示不限制标题
# 你可能需要根据实际应用找到正确的类名或标题
#hwnd = win32gui.FindWindow("Notepad", None)


# 交互式焦点选择
countdown = 3
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


if hwnd:
    print(f"找到记事本窗口，句柄为: {hwnd}")

    # 2. 发送按键消息
    # 模拟按下 'A' 键
    # VK_A 是 'A' 键的虚拟键码 (0x41)
    # WM_KEYDOWN 是按键按下的消息类型
    # lParam 参数通常包含扫描码和一些标志位。对于 PostMessage/SendMessage，
    # 如果只模拟简单的按键，lParam 可以构造如下：
    # bits 0-15: 重复次数 (通常是 1)
    # bits 16-23: OEM 扫描码 (需要查阅，但对于常见键通常可以省略或置0，系统会计算)
    # bit 24: 扩展键标志 (例如，方向键、小键盘Enter等需要置1)
    # bits 25-28: 上下文代码 (通常是 0)
    # bit 29: 之前的键状态 (如果是重复按键则置1)
    # bit 30: 转换状态 (如果是释放键则置1)
    # bit 31: 转换状态 (如果是释放键则置1)

    # 对于简单的 VK_A，lParam 可以这样构造 (重复1次):
    lParam_keydown = 1 # 重复次数
    # 这里省略扫描码和标志位的复杂构造，对于很多应用 PostMessage/SendMessage
    # 只需要 VK 码和简单的 lParam 即可
    # 更完整的 lParam_keydown 可以通过 SendInput 结构推导，但对于 PostMessage
    # 简化 often works. A common simple structure for lParam for WM_KEYDOWN:
    # bits 0-15: repeat count (1)
    # bits 16-23: scan code (system derives or needs to be correct)
    # bit 24: extended-key flag (0 or 1)
    # bit 29: previous key state (0 for first press)
    # bit 31: transition state (0 for key down)
    # Let's use a common simplified approach for lParam for WM_KEYDOWN/UP
    # A very basic lParam for VK_A (0x41) might look like this (assuming non-extended, repeat 1, prev state 0, transition 0):
    # Scan code for A is 0x1E (decimal 30)

    #scan_code_A = 0x1E
    #lParam_keydown = (scan_code_A << 16) | 1 # Repeat count 1

    # F11 键的参数
    vk_f11 = win32con.VK_F11   # F11 的虚拟键码
    scan_code_f11 = 0x57       # F11 的扫描码

    # 构造 lParam 参数
    # WM_KEYDOWN 的 lParam: (扫描码 << 16) | 重复次数
    lParam_f11_keydown = (scan_code_f11 << 16) | 1 # 重复次数为 1


    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_f11, lParam_keydown)
    print("发送 WM_KEYDOWN (VK_A) 消息")

    # 稍作延迟
    time.sleep(0.1)

    # 模拟抬起 'A' 键
    # WM_KEYUP 是按键抬起的消息类型
    # lParam for WM_KEYUP:
    # bits 0-15: repeat count (1)
    # bits 16-23: OEM scan code
    # bit 24: extended-key flag
    # bits 25-28: context code
    # bit 29: previous key state (1 for key up, since it was down)
    # bit 30: transition state (1 for key up)
    # bit 31: transition state (1 for key up)

    # For VK_A Key Up (assuming non-extended, repeat 1, prev state 1, transition 1):
    #lParam_keyup = (scan_code_A << 16) | 0xC0000001 # Scan code, prev state 1, transition state 1, repeat 1

    # WM_KEYUP 的 lParam: (扫描码 << 16) | 标志位 | 重复次数
    # 标志位 0xE0000000 (包含了前一个键状态和转换状态的标志)
    lParam_f11_keyup = (scan_code_f11 << 16) | 0xE0000000 | 1 # 标志位 + 重复次数 1

    #win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32api.VkKeyScan('A'), lParam_keyup)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_f11, lParam_f11_keyup)
    print("发送 WM_KEYUP (VK_A) 消息")

else:
    print("未找到记事本窗口。请确保记事本已打开。")

# 示例 (发送鼠标左键点击):
# 假设我们要点击窗口内部的某个坐标 (100, 200)
if hwnd:
    # WM_LBUTTONDOWN: 鼠标左键按下
    # wParam: 控制键状态 (Shift, Ctrl, etc.) - 0 表示无修饰键
    # lParam: 鼠标指针的 x, y 坐标 (低16位是x，高16位是y)
    mouse_x, mouse_y = 100, 200
    #lParam_mousedown = win32api.MAKELPARAM(mouse_x, mouse_y)
    lParam_mousedown = (mouse_y << 16) | (mouse_x & 0xFFFF)
    wParam_mousedown = 0 # No modifier keys

    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, wParam_mousedown, lParam_mousedown)
    print(f"发送 WM_LBUTTONDOWN ({mouse_x},{mouse_y})")

    time.sleep(0.1) # 稍作延迟

    # WM_LBUTTONUP: 鼠标左键抬起
    # wParam: 控制键状态
    # lParam: 鼠标指针的 x, y 坐标
    #lParam_mouseup = win32api.MAKELPARAM(mouse_x, mouse_y)
    lParam_mouseup = (mouse_y << 16) | (mouse_x & 0xFFFF)
    wParam_mouseup = 0 # No modifier keys

    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, wParam_mouseup, lParam_mouseup)
    print(f"发送 WM_LBUTTONUP ({mouse_x},{mouse_y})")

