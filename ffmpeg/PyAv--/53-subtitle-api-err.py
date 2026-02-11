
import av
from fractions import Fraction
import time

class MKVSubtitleStreamer:
    def __init__(self, container, stream_name="实时解说", font_size=28):
        self.container = container

        self.stream = self.container.add_stream("ass")
        
        # 2. 构造极其标准的 ASS Header
        # ASS字幕格式需要特殊头部
        ass_header = (
            "[Script Info]\n"
            "Title: Auto-generated\n"
            "ScriptType: v4.00\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding\n"
            "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1.0,1\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Text\n"
        )

        # 修正：直接使用 extradata，而不是 parameters.extradata
        self.stream.extradata = ass_header.encode('utf-8')

        # 4. 设置其他元数据
        self.stream.disposition = 1  # 默认显示
        self.stream.metadata['title'] = stream_name
        
        self._read_order = 0
        self._start_time = None

    def write(self, text, duration_ms=2000, pts_ms=None):
        if self._start_time is None:
            self._start_time = time.time()
        if pts_ms is None:
            pts_ms = int((time.time() - self._start_time) * 1000)

        # 构造数据包 (Packet)
        # 格式: ReadOrder, Layer, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        ass_line = f"{self._read_order},0,Default,,0,0,0,,{text}".encode('utf-8')

        packet = av.Packet(ass_line)
        packet.pts = pts_ms
        packet.dts = pts_ms
        packet.duration = duration_ms
        packet.stream = self.stream

        self.container.mux(packet)
        self._read_order += 1

# --- 使用示例 ---

def main():
    # 1. 打开输出文件
    output_path = "smart_subtitles.mkv"
    container = av.open(output_path, mode='w')

    # 2. 初始化我们的字幕封装类
    # 颜色设为亮黄色 (&H00FFFF)，字体大一点
    sub_handler = MKVSubtitleStreamer(
        container, 
        stream_name="实时解说", 
        #font_size=32, 
    )

    print("开始录制实时字幕...")
    try:
        for i in range(5):
            content = f"实时播报 #{i+1}: 传感器数值 {i*1.5} | {time.strftime('%H:%M:%S')}"
            
            # 写入字幕：显示 1.5 秒，自动计算当前时间点
            sub_handler.write(content, duration_ms=1500)
            
            print(f"已写入: {content}")
            time.sleep(1) # 模拟实时间隔

    finally:
        # 3. 关闭容器
        container.close()
        print(f"保存成功: {output_path}")

if __name__ == "__main__":
    main()
