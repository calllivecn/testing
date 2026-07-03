import tkinter as tk
from datetime import datetime
import threading
import time


class ClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动态时钟")
        #self.root.geometry("420x200")
        #self.root.resizable(False, False)

        self.time_var = tk.StringVar()
        self.date_var = tk.StringVar()

        # 共享数据（子线程写，主线程读）
        self._time_str = ""
        self._date_str = ""

        tk.Label(
            self.root,
            textvariable=self.date_var,
            font=("Microsoft YaHei", 14),
            fg="#666666",
        ).pack(pady=(20, 0))

        tk.Label(
            self.root,
            textvariable=self.time_var,
            font=("Consolas", 42, "bold"),
            fg="#222222",
        ).pack(pady=(5, 0))

    # -------- 子线程：只计算数据，不碰 Tkinter --------
    def _clock_worker(self):
        while True:
            now = datetime.now()
            self._time_str = now.strftime("%H:%M:%S")
            self._date_str = now.strftime("%Y年%m月%d日 周%w")
            time.sleep(0.2)

    # -------- 主线程：定时从共享数据读取并更新 UI --------
    def _poll_clock(self):
        self.time_var.set(self._time_str)
        self.date_var.set(self._date_str)
        self.root.after(200, self._poll_clock)  # ✅ 主线程中调用，安全

    def run(self):
        # 启动子线程（只做计算）
        th = threading.Thread(target=self._clock_worker, daemon=True)
        th.start()
        # 启动主线程轮询
        self._poll_clock()
        self.root.mainloop()


if __name__ == "__main__":
    app = ClockApp()
    app.run()
