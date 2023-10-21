
import av

in_vidoe="/home/zx/samba/rw/video/ipcamera/auto-split-30m_0001.mkv"
out_vidoe="/home/zx/samba/rw/video/ipcamera/auto-split-30m_0001-metadata.mkv"

# 打开一个视频文件
container = av.open(in_vidoe)
# container = av.open(in_vidoe)

# 获取元数据字典
metadata = container.metadata
print(f"{metadata=}")

# 设置元数据信息
metadata['title'] = '测试修改标题'
metadata['author'] = '我是作者'
metadata['description'] = '视频的剧情简介'
metadata['comment'] = '这是说明？'
metadata['date'] = '2023-10-21'

# 保存元数据信息到文件
container.close()
