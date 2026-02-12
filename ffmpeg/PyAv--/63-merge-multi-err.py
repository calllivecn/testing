
import sys
import heapq
from pathlib import Path
from itertools import count

import av

av.logging.set_level(av.logging.DEBUG)

def sorted_demux(in_container, srt_container):

    c = count()
    v = in_container.streams.video[0]
    a = in_container.streams.audio[0]
    s = srt_container.streams.subtitles[0]

    # 初始化迭代器和缓存
    iter_v = iter(in_container.demux(v))
    iter_a = iter(in_container.demux(a))
    iter_s = iter(srt_container.demux(s))
    
    # 缓存下一个包
    packet_v = next(iter_v, None)
    packet_a = next(iter_a, None)
    packet_s = next(iter_s, None)

    while packet_v or packet_a or packet_s:
        # 构建一个包含所有可用包的列表
        packets = []

        if packet_v: 
            if packet_v.pts is not None:
                pts = packet_v.pts
            else:
                pts = float('inf')

            heapq.heappush(packets, (pts, next(c), v, packet_v))

        if packet_a: 
            if packet_a.pts is not None:
                pts = packet_a.pts
            else:
                pts = float('inf')

            heapq.heappush(packets, (pts, next(c), a, packet_a))

        if packet_s: 
            if packet_s.pts is not None:
                pts = packet_s.pts
            else:
                pts = float('inf')

            heapq.heappush(packets, (pts, next(c), s, packet_s))

        # 按 PTS 排序，取最小的那个
        if packets:
            _, _, stream, selected_packet = heapq.heappop(packets)
            
            # 生成这个包
            yield stream, selected_packet
            
            # 更新被消耗掉的流的缓存
            if stream == v:
                packet_v = next(iter_v, None)
            elif stream == a:
                packet_a = next(iter_a, None)
            elif stream == s:
                packet_s = next(iter_s, None)
        else:
            break


def loop_demux(in_v, v, in_a, a, in_s, s):
    """
    loop_demux 的 Docstring
    
    这种只是交替输出，但是 ffmpeg -c copy 的合并是按pts 排序，取最小的那个。
    """
    v_open = True
    a_open = True
    s_open = True

    while (v_open or a_open or s_open):

        if v_open:
            try:
                p: av.Packet = next(in_v)
                yield (v, p)
            except StopIteration:
                v_open = False
            
        if a_open:
            try:
                p: av.Packet = next(in_a)
                yield (a, p)
            except StopIteration:
                a_open = False

        if s_open:
            try:
                p: av.Packet = next(in_s)
                yield (s, p)
            except StopIteration:
                s_open = False
            

def mkv_live_fix_and_subtitle_merge(in_name: Path, srt_name: Path, out_name: Path):
    # 这是py3.10以上的语法。
    # 打开一个视频文件

    with (
        av.open(in_name) as in_container,
        av.open(srt_name) as srt_container,
        av.open(out_name, mode="w") as out_container
    ):

        out_container.metadata.update(in_container.metadata)

        streams_map = {}

        v = in_container.streams.video[0]
        a = in_container.streams.audio[0]
        s = srt_container.streams.subtitles[0]

        streams_map[v] = out_container.add_stream_from_template(v)
        streams_map[a] = out_container.add_stream_from_template(a)
        streams_map[s] = out_container.add_stream_from_template(s)

        # 保存元数据信息到文件
        # for stream, packet in loop_demux(in_container.demux(v), v, in_container.demux(a), a, srt_container.demux(s), s):
        for stream, packet in sorted_demux(in_container, srt_container):
            # logger.debug(f"是不是交替的?：{s.type=}") # 是的
            print(f"{packet.stream.type} {packet=}")

            if packet.pts is None and packet.size == 0:
                print(f"又有跳过的包：{packet.stream.type} {packet=}")
                continue  # 跳过无效的包

            packet.stream = streams_map[stream]
            out_container.mux(packet)



def mkv_live_fix_and_subtitle_merge2(in_name: Path, srt_name: Path, out_name: Path):
    # 这是py3.10以上的语法。
    # 打开一个视频文件
    with (
        av.open(in_name) as in_container,
        av.open(srt_name) as srt_container,
        av.open(out_name, mode="w") as out_container
    ):

        out_container.metadata.update(in_container.metadata)

        streams_map = {}

        v = in_container.streams.video[0]
        a = in_container.streams.audio[0]
        s = srt_container.streams.subtitles[0]

        streams_map[v] = out_container.add_stream_from_template(v)
        streams_map[a] = out_container.add_stream_from_template(a)
        streams_map[s] = out_container.add_stream_from_template(s)

        for packet in in_container.demux(v):
            print(f"{packet.stream.type} {packet=}")

            if packet.pts is None and packet.size == 0:
                print(f"又有跳过的包：{packet.stream.type} {packet=}")
                continue  # 跳过无效的包

            packet.stream = v
            out_container.mux(packet)

        for packet in in_container.demux(a):
            print(f"{packet.stream.type} {packet=}")

            if packet.pts is None and packet.size == 0:
                print(f"又有跳过的包：{packet.stream.type} {packet=}")
                continue  # 跳过无效的包

            packet.stream = a
            out_container.mux(packet)

        for packet in srt_container.demux(s):
            print(f"{packet.stream.type} {packet=}")

            if packet.pts is None and packet.size == 0:
                print(f"又有跳过的包：{packet.stream.type} {packet=}")
                continue  # 跳过无效的包

            packet.stream = s
            out_container.mux(packet)

# mkv_live_fix_and_subtitle_merge(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))

mkv_live_fix_and_subtitle_merge2(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
