#!/usr/bin/bash

# 使用 `ffplay` 播放包含多音轨或字幕的视频文件时，你可以通过特定的命令行选项来选择播放哪个音轨和加载哪个字幕文件。以下是具体的操作方法：
# 
# ### 选择不同的音轨
# 
# 要选择不同的音轨，可以使用 `-ast`（audio stream）参数。例如，如果你想要播放第二条音轨，可以这样指定：
# 
# ```bash
# ffplay -ast 1 your_video_file.mp4
# ```
# 
# 注意这里的索引是从0开始的，所以 `-ast 1` 实际上选择了第二个音轨。
# 
# ### 加载和选择字幕
# 
# 对于字幕，可以通过 `-vf subtitles` 参数来指定字幕文件。例如，如果有一个与视频同名但扩展名为 `.srt` 的字幕文件，你可以这样加载字幕：
# 
# ```bash
# ffplay -vf subtitles=your_video_file.srt your_video_file.mp4
# ```
# 
# 如果你想加载视频文件内部嵌入的字幕轨道，可以使用 `-sid`（subtitle stream）参数来选择具体的字幕流。例如，选择第一个字幕轨道：
# 
# ```bash
# ffplay -sid 0 your_video_file.mp4
# ```
# 
# 同样地，这里的索引也是从0开始的。
# 
# ### 快捷键操作
# 
# 在播放过程中，你也可以使用快捷键来切换音轨和字幕：
# 
# - **切换音轨**：使用 `a` 键可以在可用的音频轨道之间循环切换。
# - **切换字幕**：使用 `v` 键可以在可用的字幕轨道之间循环切换（包括关闭字幕显示）。
# 
# ### 注意事项
# 
# - 确保字幕文件格式受支持（如 `.srt`, `.ass` 等），并且编码正确以避免显示问题。
# - 如果你的视频文件和字幕文件不在同一目录下或者名称不匹配，你需要提供完整的路径给 `-vf subtitles` 参数。
# 
# 通过这些方法，你可以灵活地选择和控制 `ffplay` 中使用的音轨和字幕，以便获得最佳观看体验。

unset DISPLAY

#w_h=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$1")
#w="${w_h%x*}"
#h="${w_h#*x}"


video_stream_info=$(ffprobe -v error -select_streams v:0 -show_streams -print_format json "$1")
w=$(echo "$video_stream_info" |jsonfmt.py -d streams[0].width)
h=$(echo "$video_stream_info" |jsonfmt.py -d streams[0].height)

echo "$w $h"

ffplay -x $[w/2] -y $[h/2] "$1"

