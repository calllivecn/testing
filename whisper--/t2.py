

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
        result = model.transcribe(str(f), language="zh")
        print(result["text"])
    else:
        print(f"给出的音频文件不存在: {f}")