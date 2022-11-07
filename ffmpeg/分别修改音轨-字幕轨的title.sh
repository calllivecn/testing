
# 1 每个轨道分别指定 titile

ffmpeg -i 001.mkv -i /tmp/zx-2.ass -map 0:v -vcodec copy -metadata:g title="第001集" -map 0:a:1 -acodec copy -map 1:s,0:s -scodec copy -metadata:s:a:0 title="日语原版" -metadata:s:s:0 title="简体中文" 001-4.mkv

# ~~-metadata:s:a:0 这里没搞清楚, 这样也可以 -metadata:s:s:0~~
# 这里的 :a 和 :s 好像分别是 音轨 和 字幕轨。 :0 估计是输出文件

-disposition:a:0 default 设置输出文件默认音频
-disposition:s:0 default 设置输出文件默认字幕

# 参考
man ffmpeg /-map_metadata

