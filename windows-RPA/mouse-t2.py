import win32gui
import win32api
import win32con
import time
import sys # Used to get maximum integer value for coordinate checks

# --- 常见按键的虚拟键码、扫描码和扩展标志映射 ---
# 这不是一个完整的列表，您可以根据需要添加更多按键
# 格式: '按键名称': (虚拟键码 VK_Code, 扫描码 Scan_Code, 是否为扩展键 Is_Extended)
# 虚拟键码可以在 win32con 中查找，扫描码需要查阅键盘扫描码表
# 扩展键通常包括方向键、数字键盘上的斜杠和 Enter、Ins/Del/Home/End/PgUp/PgDown 等
KEY_MAP = {
    'A': (0x41, 0x1E, False), 'B': (0x42, 0x30, False), 'C': (0x43, 0x2E, False),
    'D': (0x44, 0x20, False), 'E': (0x45, 0x12, False), 'F': (0x46, 0x21, False),
    'G': (0x47, 0x22, False), 'H': (0x48, 0x23, False), 'I': (0x49, 0x17, False),
    'J': (0x4A, 0x24, False), 'K': (0x4B, 0x25, False), 'L': (0x4C, 0x26, False),
    'M': (0x4D, 0x32, False), 'N': (0x4E, 0x31, False), 'O': (0x4F, 0x18, False),
    'P': (0x50, 0x19, False), 'Q': (0x51, 0x10, False), 'R': (0x52, 0x13, False),
    'S': (0x53, 0x1F, False), 'T': (0x54, 0x14, False), 'U': (0x55, 0x16, False),
    'V': (0x56, 0x2F, False), 'W': (0x57, 0x11, False), 'X': (0x58, 0x2D, False),
    'Y': (0x59, 0x15, False), 'Z': (0x5A, 0x2C, False),

    '0': (0x30, 0x0B, False), '1': (0x31, 0x02, False), '2': (0x32, 0x03, False),
    '3': (0x33, 0x04, False), '4': (0x34, 0x05, False), '5': (0x35, 0x06, False),
    '6': (0x36, 0x07, False), '7': (0x37, 0x08, False), '8': (0x38, 0x09, False),
    '9': (0x39, 0x0A, False), # 主键盘数字键

    'F1': (0x70, 0x3B, False), 'F2': (0x71, 0x3C, False), 'F3': (0x72, 0x3D, False),
    'F4': (0x73, 0x3E, False), 'F5': (0x74, 0x3F, False), 'F6': (0x75, 0x40, False),
    'F7': (0x76, 0x41, False), 'F8': (0x77, 0x42, False), 'F9': (0x78, 0x43, False),
    'F10': (0x79, 0x44, False), 'F11': (0x7A, 0x57, False), 'F12': (0x7B, 0x58, False),

    'Space': (0x20, 0x39, False),
    'Enter': (0x0D, 0x1C, False), # 主键盘 Enter
    'Escape': (0x1B, 0x01, False),
    'Backspace': (0x08, 0x0E, False),
    'Tab': (0x09, 0x0F, False),

    'Left': (0x25, 0x4B, True), # 方向左键
    'Up': (0x26, 0x48, True),   # 方向上键
    'Right': (0x27, 0x4D, True),# 方向右键
    'Down': (0x28, 0x50, True), # 方向下键

    'Insert': (0x2D, 0x52, True),
    'Delete': (0x2E, 0x53, True),
    'Home': (0x24, 0x47, True),
    'End': (0x23, 0x4F, True),
    'PageUp': (0x21, 0x49, True),
    'PageDown': (0x22, 0x51, True),

    'Ctrl': (0x11, 0x1D, False), # 默认左 Ctrl，右 Ctrl 扫描码不同且是扩展键 (0x9D)
    'Alt': (0x12, 0x38, False),  # 默认左 Alt，右 Alt 扫描码不同且是扩展键 (0xB8)
    'Shift': (0x10, 0x2A, False),# 默认左 Shift，右 Shift 扫描码不同 (0x36)

    # 数字小键盘键 (NumPad) - 通常是扩展键，有专门的 VK 码或与主键盘共享 VK 码但扫描码不同
    'NumPad0': (0x60, 0x52, True), 'NumPad1': (0x61, 0x4F, True),
    'NumPad2': (0x62, 0x50, True), 'NumPad3': (0x63, 0x51, True),
    'NumPad4': (0x64, 0x4B, True), 'NumPad5': (0x65, 0x4C, True),
    'NumPad6': (0x66, 0x4D, True), 'NumPad7': (0x67, 0x47, True),
    'NumPad8': (0x68, 0x48, True), 'NumPad9': (0x69, 0x49, True),
    'Multiply': (0x6A, 0x37, False), # NumPad *
    'Add': (0x6B, 0x4E, False),    # NumPad +
    'Separator': (0x6C, 0x53, False), # NumPad . or Del
    'Subtract': (0x6D, 0x4A, False), # NumPad -
    'Decimal': (0x6E, 0x53, False),  # NumPad .
    'Divide': (0x6F, 0x35, True),   # NumPad /
    'NumPadEnter': (0x0D, 0x9C, True), # 数字小键盘 Enter (VK_RETURN 但扫描码不同且是扩展键)
}


class WindowMessenger:
    """
    用于向指定 Windows 窗口发送虚拟鼠标和键盘事件的类库。
    使用 PostMessage 实现，通常在目标窗口无焦点时也能工作。
    """

    def __init__(self, hwnd):
        """
        初始化 WindowMessenger 实例。

        Args:
            hwnd: 目标窗口的句柄 (HWND)。
                  如果 hwnd 为 0 或无效，将引发 ValueError。
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise ValueError(f"无效的窗口句柄: {hwnd}")
        self.hwnd = hwnd

    # --- 静态方法：查找窗口句柄 ---
    @staticmethod
    def find_window(class_name=None, window_title=None):
        """
        通过窗口类名和/或窗口标题查找窗口句柄。

        Args:
            class_name: 窗口的类名 (字符串)，可为 None。
            window_title: 窗口的标题 (字符串)，可为 None。

        Returns:
            窗口句柄 (HWND)，如果未找到则返回 0。
        """
        hwnd = win32gui.FindWindow(class_name, window_title)
        if not hwnd:
            print(f"警告: 未找到类名为'{class_name}', 标题为'{window_title}'的窗口。")
        return hwnd

    @staticmethod
    def get_key_codes(key_name):
         """
         根据常见的按键名称查找其虚拟键码、扫描码和扩展标志。

         Args:
             key_name: 按键的字符串名称 (例如 'A', 'F11', 'Space', 'Left')。

         Returns:
             一个元组 (vk_code, scan_code, is_extended)，如果未找到则返回 None。
         """
         return KEY_MAP.get(key_name)


    # --- 内部方法：检查句柄是否有效 ---
    def _is_handle_valid(self):
        """检查当前存储的窗口句柄是否仍然有效。"""
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
             print(f"错误: 窗口句柄 {self.hwnd} 已失效。")
             self.hwnd = 0 # 将失效句柄清零
             return False
        return True

    # --- 键盘事件方法 ---
    def send_key_down(self, vk_code, scan_code, is_extended=False, repeat_count=1):
        """
        向窗口发送 WM_KEYDOWN 消息 (按键按下)。

        Args:
            vk_code: 按键的虚拟键码 (例如 win32con.VK_A)。
            scan_code: 按键的扫描码。
            is_extended: 布尔值，指示是否为扩展键。
            repeat_count: 按键重复次数，默认为 1。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        # 构造 lParam for WM_KEYDOWN
        # bits 0-15: 重复次数 (repeat_count)
        # bits 16-23: 扫描码 (scan_code)
        # bit 24: 扩展键标志 (is_extended ? 1 : 0)
        # bits 25-31: 0 (对于 WM_KEYDOWN 通常是这样)

        lParam = (scan_code << 16) | repeat_count
        if is_extended:
            lParam |= (1 << 24) # 设置扩展键标志

        # wParam 是虚拟键码
        wParam = vk_code

        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, wParam, lParam)
        # print(f"Posted WM_KEYDOWN: VK={vk_code}, Scan={scan_code}, Ext={is_extended}, hWnd={self.hwnd}")
        return True

    def send_key_up(self, vk_code, scan_code, is_extended=False, repeat_count=1):
        """
        向窗口发送 WM_KEYUP 消息 (按键抬起)。

        Args:
            vk_code: 按键的虚拟键码。
            scan_code: 按键的扫描码。
            is_extended: 布尔值，指示是否为扩展键。
            repeat_count: 按键重复次数，默认为 1。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        # 构造 lParam for WM_KEYUP
        # bits 0-15: 重复次数 (repeat_count)
        # bits 16-23: 扫描码 (scan_code)
        # bit 24: 扩展键标志 (is_extended ? 1 : 0)
        # bit 29: 前一个键状态 (总是 1 表示之前是按下状态)
        # bit 30: 转换状态 (总是 1 表示从按下到抬起)
        # bit 31: 转换状态 (总是 1，与 bit 30 一起表示抬起)
        # 组合起来，标志位通常是 (1<<29) | (1<<30) | (1<<31) = 0xE0000000

        flags = (1 << 29) | (1 << 30) | (1 << 31) # 0xE0000000
        if is_extended:
             flags |= (1 << 24) # 添加扩展键标志 0x01000000

        lParam = (scan_code << 16) | flags | repeat_count

        wParam = vk_code

        win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, wParam, lParam)
        # print(f"Posted WM_KEYUP: VK={vk_code}, Scan={scan_code}, Ext={is_extended}, hWnd={self.hwnd}")
        return True

    def send_key_press(self, vk_code, scan_code, is_extended=False, delay=0.05, repeat_count=1):
        """
        模拟完整的按键按下和抬起过程。

        Args:
            vk_code: 按键的虚拟键码。
            scan_code: 按键的扫描码。
            is_extended: 布尔值，指示是否为扩展键。
            delay: 按下和抬起之间的延迟时间 (秒)。
            repeat_count: 按键重复次数，默认为 1。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
            return False
        if not self.send_key_down(vk_code, scan_code, is_extended, repeat_count):
            return False
        time.sleep(delay)
        return self.send_key_up(vk_code, scan_code, is_extended, repeat_count)

    def send_key_by_name(self, key_name, delay=0.05, repeat_count=1):
        """
        根据按键名称发送按键按下和抬起模拟。

        Args:
            key_name: KEY_MAP 中定义的按键名称字符串。
            delay: 按下和抬起之间的延迟时间 (秒)。
            repeat_count: 按键重复次数，默认为 1。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        key_info = self.get_key_codes(key_name)
        if not key_info:
            print(f"错误: 未找到按键名称 '{key_name}' 的信息。")
            return False
        vk_code, scan_code, is_extended = key_info
        return self.send_key_press(vk_code, scan_code, is_extended, delay, repeat_count)


    # --- 鼠标事件方法 ---
    def send_mouse_move(self, x, y, flags=0):
        """
        向窗口发送 WM_MOUSEMOVE 消息。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标 (相对于窗口客户区左上角)。
            y: 鼠标的 Y 坐标 (相对于窗口客户区左上角)。
            flags: 鼠标键和修饰键的状态 (如 win32con.MK_LBUTTON, win32con.MK_SHIFT)，默认为 0。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        # 构造 lParam: (y << 16) | x
        # 确保 x 和 y 在 16 位范围内，虽然通常坐标不会超出
        if x < 0 or y < 0 or x > 0xFFFF or y > 0xFFFF:
             # 简单处理超出范围的坐标，更严格可以 raise ValueError
             print(f"警告: 鼠标坐标 ({x},{y}) 超出 16 位范围，可能不准确。")

        lParam = (y << 16) | (x & 0xFFFF) # 手动计算 MAKELPARAM
        # wParam 是鼠标键和修饰键的状态
        wParam = flags

        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, wParam, lParam)
        # print(f"Posted WM_MOUSEMOVE: ({x},{y}), Flags={flags}, hWnd={self.hwnd}")
        return True

    def send_lbutton_down(self, x, y, flags=0):
        """
        向窗口发送 WM_LBUTTONDOWN 消息 (鼠标左键按下)。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            flags: 修饰键状态 (如 win32con.MK_SHIFT, win32con.MK_CONTROL)，发送 DOWN 时通常不包含 MK_LBUTTON。默认为 0。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        lParam = (y << 16) | (x & 0xFFFF) # 手动计算 MAKELPARAM
        # wParam 是修饰键状态
        wParam = flags

        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, wParam, lParam)
        # print(f"Posted WM_LBUTTONDOWN: ({x},{y}), Flags={flags}, hWnd={self.hwnd}")
        return True

    def send_lbutton_up(self, x, y, flags=0):
        """
        向窗口发送 WM_LBUTTONUP 消息 (鼠标左键抬起)。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            flags: 修饰键状态，发送 UP 时通常不包含 MK_LBUTTON。默认为 0。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        lParam = (y << 16) | (x & 0xFFFF) # 手动计算 MAKELPARAM
        # wParam 是修饰键状态
        wParam = flags

        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, wParam, lParam)
        # print(f"Posted WM_LBUTTONUP: ({x},{y}), Flags={flags}, hWnd={self.hwnd}")
        return True

    def send_lbutton_click(self, x, y, delay=0.05, flags=0):
        """
        模拟完整的鼠标左键点击过程 (按下后抬起)。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            delay: 按下和抬起之间的延迟时间 (秒)。
            flags: 修饰键状态。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
            return False
        if not self.send_lbutton_down(x, y, flags):
            return False
        time.sleep(delay)
        return self.send_lbutton_up(x, y, flags)

    # --- 右键事件方法 ---
    def send_rbutton_down(self, x, y, flags=0):
        """
        向窗口发送 WM_RBUTTONDOWN 消息 (鼠标右键按下)。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            flags: 修饰键状态。默认为 0。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        lParam = (y << 16) | (x & 0xFFFF)
        wParam = flags

        win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, wParam, lParam)
        return True

    def send_rbutton_up(self, x, y, flags=0):
        """
        向窗口发送 WM_RBUTTONUP 消息 (鼠标右键抬起)。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            flags: 修饰键状态。默认为 0。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
             return False

        lParam = (y << 16) | (x & 0xFFFF)
        wParam = flags

        win32api.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, wParam, lParam)
        return True

    def send_rbutton_click(self, x, y, delay=0.05, flags=0):
        """
        模拟完整的鼠标右键点击过程。坐标是相对于窗口客户区的。

        Args:
            x: 鼠标的 X 坐标。
            y: 鼠标的 Y 坐标。
            delay: 按下和抬起之间的延迟时间 (秒)。
            flags: 修饰键状态。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
            return False
        if not self.send_rbutton_down(x, y, flags):
            return False
        time.sleep(delay)
        return self.send_rbutton_up(x, y, flags)

    def send_lbutton_click_current(self, delay=0.05, flags=0):
        """
        在当前鼠标指针位置对目标窗口发送左键点击。
        首先获取当前鼠标位置，然后转换为窗口客户区坐标再发送消息。

        Args:
            delay: 按下和抬起之间的延迟时间 (秒)。
            flags: 修饰键状态。

        Returns:
            发送成功返回 True，否则返回 False。
        """
        if not self._is_handle_valid():
            return False

        # 1. 获取当前鼠标屏幕坐标
        try:
            screen_x, screen_y = win32api.GetCursorPos()
        except Exception as e:
            print(f"错误: 无法获取当前鼠标位置 - {e}")
            return False

        # 2. 将屏幕坐标转换为目标窗口的客户区坐标
        try:
            client_x, client_y = win32gui.ScreenToClient(self.hwnd, (screen_x, screen_y))
        except Exception as e:
             print(f"错误: 无法将屏幕坐标 ({screen_x},{screen_y}) 转换为窗口 {self.hwnd} 的客户区坐标 - {e}")
             return False


        # 3. 使用客户区坐标发送点击消息
        print(f"在当前鼠标位置 ({screen_x},{screen_y}) (客户区: {client_x},{client_y}) 对窗口 {self.hwnd} 发送左键点击...")
        return self.send_lbutton_click(client_x, client_y, delay, flags)

    # 您可以类似地添加 send_rbutton_click_current 等方法

# --- 您可以类似地添加 send_mbutton_down/up/click 方法 ---
# wm_mbuttondown = win32con.WM_MBUTTONDOWN
# wm_mbuttonup = win32con.WM_MBUTTONUP
# mk_mbutton = win32con.MK_MBUTTON


# --- 如何使用这个类库的示例 ---
if __name__ == "__main__":
    # 查找记事本窗口 (假设它已打开)
    # notepad_hwnd = WindowMessenger.find_window(class_name="Notepad")
    # notepad_hwnd = WindowMessenger.find_window(window_title="无标题 - 记事本") # 如果标题确定的话

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


    if hwnd:
        try:
            # 创建 WindowMessenger 实例
            messenger = WindowMessenger(hwnd)

            print("\n--- 键盘事件示例 ---")

            # 发送 'H' 键
            print("发送 'H' 键...")
            messenger.send_key_by_name('H')
            time.sleep(0.5)

            messenger.send_key_by_name('B')
            time.sleep(0.5)

            messenger.send_key_by_name('Enter')
            time.sleep(0.5)
            sys.exit(0)

            # 发送 'ello World!' 字符 (注意：这需要应用程序能响应低级键消息)
            # 发送单个字符通常比直接发送 WM_CHAR 更复杂，因为需要处理 Shift 等
            # 对于简单的字符，可以查表发送 VK_CODE，但字符输入更推荐 SendInput 或特定的库
            # 这里仅作为示例，实际输入文本可能需要更复杂的逻辑或使用其他库
            text_to_send = "ello World!"
            print(f"尝试发送文本 '{text_to_send}' (可能不完美)...")
            for char in text_to_send:
                 # 对于简单的字符，可以尝试查找其 VK/Scan 码并发送按键事件
                 char_upper = char.upper()
                 if char_upper in KEY_MAP:
                      key_info = WindowMessenger.get_key_codes(char_upper)
                      if key_info:
                           vk, scan, is_ext = key_info
                           # 简单处理 Shift：如果字符是大写且不是 Ctrl/Alt/Shift 本身，假设需要 Shift
                           # 这是一个简化的处理，不适用于所有情况和所有字符
                           needs_shift = char.isupper() and char_upper not in ['CTRL', 'ALT', 'SHIFT']
                           if needs_shift:
                                messenger.send_key_down(win32con.VK_SHIFT, 0x2A) # 假定左 Shift 扫描码 0x2A
                                time.sleep(0.02)

                           messenger.send_key_press(vk, scan, is_extended=is_ext, delay=0.02)

                           if needs_shift:
                                time.sleep(0.02)
                                messenger.send_key_up(win32con.VK_SHIFT, 0x2A) # 抬起 Shift
                           time.sleep(0.02) # 字符间隔

                 elif char == ' ': # 处理空格
                      messenger.send_key_by_name('Space', delay=0.02)
                 # 其他特殊字符处理会更复杂...
            print("\n文本发送尝试结束。")

            time.sleep(1)

            # 发送 Enter 键
            print("发送 Enter 键...")
            messenger.send_key_by_name('Enter')
            time.sleep(0.5)

            # 发送 F5 键 (通常在记事本中是刷新)
            print("发送 F5 键...")
            messenger.send_key_by_name('F5')
            time.sleep(1)


            print("\n--- 鼠标事件示例 ---")
            # 注意: 坐标 (x, y) 是相对于窗口客户区的左上角 (0, 0)

            # 发送左键点击到坐标 (100, 100)
            print("发送左键点击到 (100, 100)...")
            messenger.send_lbutton_click(100, 100)
            time.sleep(1)

            # 发送右键点击到坐标 (150, 150)
            print("发送右键点击到 (150, 150)...")
            messenger.send_rbutton_click(150, 150)
            time.sleep(1)

            # 移动鼠标到坐标 (200, 200) (不会点击)
            print("移动鼠标到 (200, 200)...")
            messenger.send_mouse_move(200, 200)
            time.sleep(1)

            print("\n示例执行完毕。")


        except ValueError as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"发生其他错误: {e}")

    else:
        print("未找到记事本窗口，跳过示例。请打开记事本后重试。")

