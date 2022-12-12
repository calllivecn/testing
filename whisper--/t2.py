

import time
from pathlib import Path

try:
    import readline
except Exception:
    pass


import whisper

# model = whisper.load_model("base")
# model = whisper.load_model("small")
model = whisper.load_model("medium")

while (filename := input("输入音频(.exit 退出): ")) != ".exit":
    f = Path(filename)
    if f.exists():
        start = time.time()
        result = model.transcribe(str(f), language="zh")
        end = time.time()
        print(f"耗时：{end-start}/s")
        print(f"转录文本：{result['text']}")
    else:
        print(f"给出的音频文件不存在: {f}")