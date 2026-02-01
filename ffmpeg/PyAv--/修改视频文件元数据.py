
import sys
from datetime import datetime

import av


in_vidoe="auto-split-30m_0001.mkv"
out_vidoe="auto-split-30m_0001-metadata.mkv"

if len(sys.argv) < 3:
    print("用法: python script.py <输入文件> <输出文件>")
    sys.exit(1)

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
    metadata['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata['DIY metadata'] = '好像可以随便写？？？？？是的!'
    
    # 在新文件里打开新的流
    stream_map = {}
    for s in in_container.streams:
        print(f"stream: {s} type:{s.type}")
        # 这是新版的写法 v16.1.0
        # 关键：将输入流 index 映射到输出流对象
        stream_map[s.index] = out_container.add_stream_from_template(s)

    
    # 保存元数据信息到文件
    for packet in in_container.demux():

        if packet.pts is None:
            print(f"跳过无 pts 的包: {packet=}")
            continue  # 跳过无效的包

        packet.stream = stream_map[packet.stream.index]

        out_container.mux(packet)

print("处理完成，已保存到:", out_vidoe)

