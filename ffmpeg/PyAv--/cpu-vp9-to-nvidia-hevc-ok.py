
# 使用的av v16.0.1
import av
import sys
import time

def vp9_to_hevc_soft_decode(input_path: str, output_path: str):
    # 1. 打开输入（自动软解 VP9）
    input_container = av.open(input_path)
    video_stream = input_container.streams.video[0]
    
    width = video_stream.width
    height = video_stream.height
    fps = video_stream.average_rate
    print(f"🎥 软解 VP9: {width}x{height} @ {fps}")

    # 2. 创建输出容器
    output_container = av.open(output_path, 'w')

    # 3. 创建 HEVC 硬件编码器（GPU）
    video_out = output_container.add_stream('hevc_nvenc', rate=fps)
    video_out.width = width
    video_out.height = height
    video_out.pix_fmt = 'nv12'
    video_out.codec_context.options = {
        'preset': 'p4',
        'profile': 'main',
        'rc': 'vbr',
        'cq': '23',
        'gpu': '0'
    }

    # 4. 音频透传
    audio_out_streams = []
    for stream in input_container.streams.audio:
       audio_out = output_container.add_stream(stream.codec.name)
       audio_out_streams.append(audio_out)

    # 5. 转码主循环
    frame_count = 0
    start = time.time()
    print("🚀 开始转码 (VP9 软解 → HEVC 硬编)...")

    for packet in input_container.demux():
        if packet.stream.type == 'video':
            for frame in packet.decode():
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"  → 帧: {frame_count}")
                
                # 转为 nv12（CPU → GPU 上传）
                frame = frame.reformat(width, height, 'nv12')
                for enc_pkt in video_out.encode(frame):
                    output_container.mux(enc_pkt)
                    
        #elif packet.stream.type == 'audio':
        #    idx = input_container.streams.audio.index(packet.stream)
        #    packet.stream = audio_out_streams[idx]
        #    output_container.mux(packet)

    # 6. 冲洗
    for enc_pkt in video_out.encode():
        output_container.mux(enc_pkt)

    input_container.close()
    output_container.close()
    print(f"✅ 完成! {frame_count} 帧 | 耗时 {time.time() - start:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python transcode.py <input> <output>")
        sys.exit(1)
    vp9_to_hevc_soft_decode(sys.argv[1], sys.argv[2])
