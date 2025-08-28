
import sys

import av


in_vidoe="auto-split-30m_0001.mkv"
out_vidoe="auto-split-30m_0001-metadata.mkv"

in_vidoe=sys.argv[1]
out_vidoe=sys.argv[2]

# 这是py3.10以上的语法。
# 打开一个视频文件
with (
        av.open(in_vidoe) as in_container,
        av.open(out_vidoe, mode="w") as out_container
):

    metadata = out_container.metadata
    print(f"{in_container.metadata=}")
    
    # 设置元数据信息
    metadata['title'] = '测试修改标题'
    metadata['author'] = '我是作者'
    metadata['description'] = '视频的剧情简介'
    metadata['comment'] = '这是说明？'
    metadata['date'] = '2023-10-21'
    metadata['DIY metadata'] = '好像可以随便写？？？？？是的'
    
    # 在新文件里打开新的流
    out_streams = {}
    for s in in_container.streams:
        print(f"stream: {s} type:{s.type}")
        out_streams[s.type] = out_container.add_stream(template=s)
    
    # 保存元数据信息到文件
    for packet in in_container.demux():
        out_container.mux(packet)

