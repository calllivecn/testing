import av
from fractions import Fraction
import time

# 1. 初始化容器
output_path = 'manual_subtitles.mkv'
container = av.open(output_path, mode='w')

# 2. 添加 ASS 字幕流
# 这里的 'ass' 是 codec 名称
stream = container.add_stream('ass')
stream.time_base = Fraction(1, 1000) # 毫秒基准

# 注意：对于字幕流，有时需要设置流的全局 Header (ASS Header)
# 这里我们设置一个简单的默认样式头
# stream.codec_context.extradata = (
config = (
    b"[Script Info]\nScriptType: v4.00+\n\n"
    b"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    b"Style: Default,Arial,20,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,1,1,2,10,10,10,0\n\n"
    b"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)

def write_subtitle_direct():
    start_time = time.time()
    
    first = True
    for i in range(5):
        print(f"正在生成第 {i+1} 条字幕...")
        
        # 计算时间戳 (毫秒)
        current_pts = int((time.time() - start_time) * 1000)
        duration_ms = 2000 
        
        # 字幕内容
        text = f"这是手动构造的 Packet {i+1} - {time.strftime('%H:%M:%S')}"
        
        # MKV/ASS Packet 的数据格式通常是: "ReadOrder, Layer, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        # 其中 ReadOrder 通常由容器处理，我们可以从 Layer 开始写
        # 格式: Layer, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        ass_line = f"0,Default,,0,0,0,,{text}".encode('utf-8')
        
        # 3. 核心步骤：手动创建 av.Packet
        # 直接将 bytes 传入 Packet 构造函数
        if first:
            first = False
            ass_line = config + ass_line
        packet = av.Packet(ass_line)
        
        # 4. 手动设置 Packet 的属性
        packet.pts = current_pts
        packet.dts = current_pts
        packet.duration = duration_ms
        packet.stream = stream  # 关联到字幕流
        
        # 5. 直接写入容器，跳过 encode 步骤
        container.mux(packet)
        
        time.sleep(1)

try:
    write_subtitle_direct()
finally:
    container.close()
    print(f"写入完成: {output_path}")
