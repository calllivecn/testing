import tkinter as tk
from datetime import datetime
import threading

"""
在子线程中更新UI在高版本 tkinter 中会失败。
"""


class ClockApp:
    #def __init__(self, root: tk.Tk):
    def __init__(self):
        #self.root = root
        self.root = tk.Tk()
        self.root.title("动态时钟")
        self.root.geometry("420x200")
        self.root.resizable(False, False)

        # ---------- StringVar 用于存储时间字符串 ----------
        self.time_var = tk.StringVar()
        self.date_var = tk.StringVar()

        # ---------- 日期标签 ----------
        date_label = tk.Label(
            self.root,
            textvariable=self.date_var,
            font=("Microsoft YaHei", 14),
            fg="#666666",
        )
        date_label.pack(pady=(20, 0))

        # ---------- 时间标签 ----------
        time_label = tk.Label(
            self.root,
            textvariable=self.time_var,
            font=("Consolas", 42, "bold"),
            fg="#222222",
        )
        time_label.pack(pady=(5, 0))

        # ---------- 启动定时更新 ----------
        #self._update_clock()


    def _update_clock(self):
        """每 200ms 刷新一次时间"""
        now = datetime.now()
        self.time_var.set(now.strftime("%H:%M:%S"))
        self.date_var.set(now.strftime("%Y年%m月%d日  %A"))
        # 每 200 毫秒调用一次自身，实现动态更新
        self.root.after(200, self._update_clock)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    #root = tk.Tk()
    #app = ClockApp(root)
    #root.mainloop()

    app = ClockApp()

    th = threading.Thread(target=app._update_clock, daemon=True)
    th.start()

    app.run()
