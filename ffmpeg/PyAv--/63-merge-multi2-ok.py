import heapq
import sys


import av

def merge_media_files(video_path: str, subtitle_path: str, output_path: str):
    """
    使用 PyAV v16+ API 合并视频文件和字幕文件 (相当于 ffmpeg -c copy)
    """
    # 1. 使用上下文管理器同时打开所有文件
    # PyAV 的新最佳实践建议尽可能保持文件句柄在 Context 中管理
    with av.open(video_path, mode='r') as input_video, \
         av.open(subtitle_path, mode='r') as input_sub, \
         av.open(output_path, mode='w') as output_container:

        print(f"打开文件:\n  视频: {video_path}\n  字幕: {subtitle_path}")

        # 用于映射 输入流 -> 输出流
        # key: input_stream 对象, value: output_stream 对象
        stream_mapping = {}

        # --- 步骤 1: 复制视频/音频流 (in1) ---
        for in_stream in input_video.streams:
            # template=in_stream 会自动复制 codec_context, extradata 等关键信息
            out_stream = output_container.add_stream_from_template(in_stream)
            stream_mapping[in_stream] = out_stream
            print(f"  [+] 添加流 #{in_stream.index} ({in_stream.type}): {in_stream.codec_context.name}")

        # --- 步骤 2: 复制字幕流 (in2) ---
        # SRT 文件通常被识别为 subtitle 类型，codec 为 'subrip'
        for in_stream in input_sub.streams:
            out_stream = output_container.add_stream_from_template(in_stream)
            
            # SRT 有时需要显式设置 metadata 语言，防止播放器识别为 'und'
            if 'language' not in out_stream.metadata:
                out_stream.metadata['language'] = 'chi'  # 假设是中文，可按需修改
            
            stream_mapping[in_stream] = out_stream
            print(f"  [+] 添加流 (字幕) #{in_stream.index}: {in_stream.codec_context.name}")

        print(f"开始混流到: {output_path} ...")

        # --- 步骤 3: 构造数据包生成器 ---
        # 我们需要区分 Packet 属于哪个文件，以便后续处理，但 heapq.merge 只需要迭代 Packet
        # 只要 Packet 对象里保留了 stream 引用，我们就能查到它属于哪个 output_stream
        
        # 定义包的排序键：DTS (解码时间戳)。如果 DTS 为 None (极其罕见)，退化为 0
        def packet_sort_key(pkt):
            return pkt.dts if pkt.dts is not None else 0

        # 创建两个解复用生成器
        # input_video.demux() 和 input_sub.demux() 会 yield 各自文件内部有序的 packet
        iter_video = input_video.demux()
        iter_sub = input_sub.demux()

        # --- 步骤 4: 智能交织 (Interleaving) ---
        # heapq.merge 极其高效，它假设输入流是有序的（当然是），
        # 并像拉链一样按 key (时间戳) 输出最小的那个包。
        # 这样避免了我们手动写 while 循环和处理 StopIteration。
        
        # 统计变量
        packet_count = 0
        
        for packet in heapq.merge(iter_video, iter_sub, key=packet_sort_key):

            if packet.pts is None:
                continue

            # 1. 找到该包对应的输出流
            # 如果 packet 来自我们没有映射的流（比如不想要的流），则跳过
            if packet.stream not in stream_mapping:
                continue

            out_stream = stream_mapping[packet.stream]

            # 2. 时间基转换 (Rescaling)
            # 这一步至关重要。输入流（如 Video）可能是 1/90000，字幕可能是 1/1000
            # 输出容器 MKV 通常是 1/1000。
            # packet.rescale_to 会就地修改 packet 的 pts/dts/duration
            # packet.rescale_to(out_stream.time_base)

            # 3. 重新指派流归属
            packet.stream = out_stream

            # 4. 写入容器 (Mux)
            output_container.mux(packet)
            
            packet_count += 1
            if packet_count % 500 == 0:
                print(f"\r  已处理 {packet_count} 个数据包...", end='', flush=True)

    print(f"\n合并完成! 输出文件位于: {output_path}")

if __name__ == "__main__":
    # 使用示例
    # 请根据实际文件名修改
    try:
        # merge_media_files("in1.mkv", "subtitle.srt", "out.mkv")
        merge_media_files(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"\n发生错误: {e}")
