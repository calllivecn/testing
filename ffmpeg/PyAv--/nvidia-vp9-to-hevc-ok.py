
# 使用的av v16.0.1
import sys
import time


import av
from av.codec.hwaccel import HWAccel, hwdevices_available

def hardware_vp9_to_hevc(input_path: str, output_path: str):

    # 检查 CUDA 是否可用
    if 'cuda' in hwdevices_available():
        # hwaccel = HWAccel(device_type='cuda', allow_software_fallback=True)
        hwaccel = HWAccel(device_type='cuda', allow_software_fallback=False)
        print("✅ 启用 CUDA 硬件解码（HWAccel）")
        input_container = av.open(input_path, hwaccel=hwaccel)
    else:
        print("⚠️ 未找到 CUDA 硬件解码支持，回退到软解")
        input_container = av.open(input_path)

    # 1. 打开输入容器
    # input_container = av.open(input_path)
    
    # 2. 获取视频流
    video_stream = input_container.streams.video[0]
    width = video_stream.width
    height = video_stream.height
    fps = video_stream.average_rate

    # 3. 创建 VP9 解码器上下文（启用 CUDA 硬解）
    
    print(f"🎥 视频: {width}x{height} @ {fps}")

    # 4. 创建输出容器
    output_container = av.open(output_path, 'w')

    # 5. 创建 HEVC 硬件编码流
    # encoder = output_container.add_stream('hevc_nvenc', template=video_stream)
    encoder = output_container.add_stream('hevc_nvenc', rate=fps)
    encoder.width = width
    encoder.height = height
    encoder.pix_fmt = 'nv12'  # NVENC 只接受 nv12
    encoder.codec_context.options = {
        'preset': 'p4',
        'profile': 'main',
        'rc': 'vbr',
        'cq': '23',
        'gpu': '0'
    }

    # 6. 音频透传
    audio_out_streams = []
    for stream in input_container.streams.audio:
        audio_out = output_container.add_stream(stream.codec.name)
        audio_out_streams.append(audio_out)

    # 7. 转码主循环
    frame_count = 0
    start_time = time.time()
    print("🚀 开始转码 (VP9 硬解 → HEVC 硬编)...")

    for packet in input_container.demux():
        if packet.stream.type == 'video':
            # 解码（可能返回 GPU 帧）
            for frame in packet.decode():
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"  → 帧: {frame_count}")
                
                # 如果是 GPU 帧（format.name == 'cuda'），需转为 nv12（仍在 GPU）
                if frame.format.name == 'cuda':
                    # 在 GPU 上转格式（高效）
                    frame = frame.reformat(width, height, 'nv12')
                else:
                    # 软解情况（fallback）
                    frame = frame.reformat(width, height, 'nv12')
                
                # 编码（GPU）
                for enc_pkt in encoder.encode(frame):
                    output_container.mux(enc_pkt)

        elif packet.stream.type == 'audio':
            idx = input_container.streams.audio.index(packet.stream)
            packet.stream = audio_out_streams[idx]
            output_container.mux(packet)

    # 8. 冲洗编码器
    for enc_pkt in encoder.encode():
        output_container.mux(enc_pkt)

    input_container.close()
    output_container.close()

    print(f"✅ 转码完成! {frame_count} 帧 | 耗时 {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python nvidia-vp9-to-hevc.py <input.mp4> <output.mkv>")
        sys.exit(1)
    hardware_vp9_to_hevc(sys.argv[1], sys.argv[2])
