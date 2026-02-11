import time
from datetime import timedelta

class SRTWriter:
    def __init__(self, filename):
        """
        初始化 SRT 写入器
        :param filename: 输出的 .srt 文件路径
        """
        self.file = open(filename, "w", encoding="utf-8")
        self.index = 1
        self._last_end_time = 0.0  # 记录上一条字幕的结束时间

    def _format_timestamp(self, seconds):
        """将秒数转换为 SRT 时间戳格式: HH:MM:SS,mmm"""
        total_seconds = float(seconds)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = total_seconds % 60
        milliseconds = int((secs - int(secs)) * 1000)
        seconds_int = int(secs)
        return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"

    def add_entry_at(self, timestamp, duration, text):
        """
        在指定绝对时间添加字幕
        :param timestamp: 开始时间（秒）
        :param duration: 持续时间（秒）
        :param text: 字幕文本
        """
        start = float(timestamp)
        end = start + float(duration)
        if end > self._last_end_time:
            self._last_end_time = end

        self._write_entry(start, end, text)

    def add_entry_now(self, t, text):
        """
        连续添加字幕：从上一条结束时间开始，持续 `time` 秒
        :param time: 显示持续时间（秒）
        :param text: 字幕文本
        """
        start = self._last_end_time
        end = start + float(t)
        self._last_end_time = end
        self._write_entry(start, end, text)

    def _write_entry(self, start, end, text):
        """内部方法：写入一条字幕条目"""
        start_str = self._format_timestamp(start)
        end_str = self._format_timestamp(end)
        self.file.write(f"{self.index}\n")
        self.file.write(f"{start_str} --> {end_str}\n")
        self.file.write(f"{text}\n\n")
        self.file.flush()
        self.index += 1

    def close(self):
        if not self.file.closed:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



if __name__ == "__main__":
    with SRTWriter("demo.srt") as srt:
        # 方式1：按绝对时间插入（可覆盖、跳跃）
        srt.add_entry_at(0.0, 2.0, "开场白")
        srt.add_entry_at(5.0, 1.5, "5秒后出现")

        # 方式2：连续追加（从上一条结束处开始）
        srt.add_entry_now(1.0, "接在 6.5s 开始，持续1秒")      # start=6.5
        srt.add_entry_now(2.0, "再接2秒\n支持换行")             # start=7.5

        # 再插一条绝对时间的（不影响连续链）
        srt.add_entry_at(10.0, 1.0, "我在10秒处！")

        # 继续连续追加（从 max(11.0, 上次_last_end=9.5) = 11.0 开始）
        srt.add_entry_now(1.5, "接在11秒后")                   # start=11.0

