import av

def record_with_audio(video_dev='/dev/video0', audio_dev='default', output_file='output.mp4'):
    # 1. 打开视频输入 (V4L2)
    v_input = av.open(video_dev, format='v4l2', options={'video_size': '640x480', 'framerate': '30'})
    v_stream = v_input.streams.video[0]

    # 2. 打开音频输入 (ALSA 或 Pulse)
    # Linux 下常用 'alsa' 或 'pulse' 格式
    try:
        a_input = av.open(audio_dev, format='pulse')
    except Exception:
        a_input = av.open(audio_dev, format='alsa')
    a_stream = a_input.streams.audio[0]

    # 3. 创建输出容器及流
    out_container = av.open(output_file, mode='w')
    
    # 添加输出视频流
    out_v = out_container.add_stream('libx264', rate=30)
    out_v.width = v_stream.width
    out_v.height = v_stream.height
    out_v.pix_fmt = 'yuv420p'

    # 添加输出音频流
    out_a = out_container.add_stream('aac', rate=a_stream.sample_rate)
    # 注意：某些音频输入可能需要重采样，这里简单演示直接配置
    out_a.layout = a_stream.layout
    out_a.format = 'fltp' # AAC 通常使用 fltp

    # 4. 同时迭代处理 (Demux & Mux)
    # 使用各自的迭代器
    v_packets = v_input.demux(v_stream)
    a_packets = a_input.demux(a_stream)

    print("开始录制，按 Ctrl+C 停止...")
    try:
        while True:
            # 这里的简单逻辑：尽可能快地从两个源抓取
            # 进阶做法可以使用线程或 select() 监听文件描述符
            try:
                # 处理视频
                v_packet = next(v_packets)
                for frame in v_packet.decode():
                    # 可以在这里做一些滤镜处理
                    for out_packet in out_v.encode(frame):
                        out_container.mux(out_packet)
                
                # 处理音频
                a_packet = next(a_packets)
                for frame in a_packet.decode():
                    for out_packet in out_a.encode(frame):
                        out_container.mux(out_packet)
            except (StopIteration, av.BlockingIOError):
                break

    except KeyboardInterrupt:
        print("\n停止录制...")
    finally:
        # 刷新缓冲区
        out_container.mux(out_v.encode(None))
        out_container.mux(out_a.encode(None))
        
        v_input.close()
        a_input.close()
        out_container.close()

if __name__ == "__main__":
    # 在 Linux 下，你可以先用 'arecord -L' 查看音频设备名
    record_with_audio()
