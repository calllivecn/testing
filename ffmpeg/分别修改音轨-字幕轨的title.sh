
# 1 每个轨道分别指定 titile

ffmpeg -i 001.mkv -i /tmp/zx-2.ass -map 0:v -vcodec copy -metadata:g title="第001集" -map 0:a:1 -acodec copy -map 1:s,0:s -scodec copy -metadata:s:a:0 title="日语原版" -metadata:s:s:0 title="简体中文" 001-4.mkv

# -metadata:s:a:0 这里没搞清楚, 这样也可以 -metadata:s:s:0 

ffmpeg -i 001.mkv -i /tmp/zx-2.ass -map 0:v -vcodec copy -metadata:g title="第001集" -map 0:a:1 -acodec copy -map 1:s,0:s -scodec copy -metadata:s:a:0 title="日语原版" -metadata:s:s:0 title="简体中文" 001-4.mkv

# 参考
man ffmpeg /-map_metadata

