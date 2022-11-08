


subtitle2(){
	if [ -f "ass/${i}.ass" ];then
		ffmpeg -hide_banner -i "ass/${i}.ass" -y /tmp/t.srt
		ffmpeg -hide_banner -i /tmp/t.srt "ass2/${i}.ass"
	fi
}

batch_task(){
	if [ -f ~/ass2/${i}.ass ];then
		#batch-task2.py -- ffmpeg -hide_banner -i "龙珠超2015蓝光/${i}.mkv" -i ~/ass2/${i}.ass -map 0:v -vcodec libx265 -metadata:s:v:0 title="第${i}集" -map 0:2 -acodec copy -metadata:s:a:0 title=日语原版 -disposition:a:0 default -map 1:s -scodec copy -metadata:s:s:0 title=简体中文 -disposition:s:0 default "龙珠超2015蓝光libx265/${i}.mkv"

		batch-task2.py -- ffmpeg -hide_banner -i "龙珠超2015蓝光/${i}.mkv" -i ~/ass2/${i}.ass -map 0:v -vcodec libx265 -metadata:s:v:0 title="第${i}集" -map 0:2 -acodec copy -metadata:s:a:0 title=日语原版 -metadata:s:a:0 language=jpn -disposition:a:0 default -map 1:s -scodec copy -metadata:s:s:0 title=简体中文 -metadata:s:s:0 language=chi -disposition:s:0 default "龙珠超2015蓝光libx265/${i}.mkv"
	fi

}

check_audio_jpn(){
	python3 ~/work/testing/ffmpeg/ffprobe2json.py "$1"
}


prefix_ro="/mnt/aliyun-fuse/net_disk/media/七龙珠/龙珠超2015蓝光"
prefix_ro2="/mnt/aliyun-fuse/net_disk/media/七龙珠/龙珠超2015蓝光libx265"
prefix_rw="/mnt/aliyun-webdav/net_disk/media/七龙珠/龙珠超2015蓝光libx265-4"

new_order_11_08(){
# 0. 1 ~ 131 if $libx265 存在
#	在看看是不是音轨错误	
#		如果是:"" ff -i $prefix_ro -i lkif -i $ass ....
#		否：ffmpeg  -vcodec copy 打上正确的标

	i="$1"
	if [ -f "$prefix_ro2/${i}.mkv" ];then
		
		# 查看是不是音轨错误
		if grep -q "${i}.mkv" ~/check-jpn.txt;then
			# 是音轨错误
			batch-task2.py -- ffmpeg -hide_banner \
				-i "$prefix_ro2/${i}.mkv" -i "$prefix_ro/${i}.mkv" \
				-map 0:v -vcodec copy -metadata:s:v:0 title="第${i}集" \
				-map 1:3 -acodec copy -metadata:s:a:0 title="日语原版" -metadata:s:a:0 language=jpn -disposition:a:0 default \
				-map 0:s -scodec copy -metadata:s:s:0 title="简体中文" -metadata:s:s:0 language=chi -disposition:s:0 default \
				"$prefix_rw/${i}.mkv"
		else
			# 不是音轨错误, 只需要修改标签
			batch-task2.py -- ffmpeg -hide_banner \
				-i "$prefix_ro2/${i}.mkv" \
				-map 0:v -vcodec copy -metadata:s:v:0 title="第${i}集" \
				-map 0:a -acodec copy -metadata:s:a:0 title="日语原版" -metadata:s:a:0 language=jpn -disposition:a:0 default \
				-map 0:s -scodec copy -metadata:s:s:0 title="简体中文" -metadata:s:s:0 language=chi -disposition:s:0 default \
				"$prefix_rw/${i}.mkv"

		fi

	else
		# 需要从新的来

		# 查看音轨是不是 3
		if grep -q "${i}.mkv" ~/check-jpn.txt;then
			# 音轨: 3
			batch-task2.py -- ffmpeg -hide_banner \
				-i "$prefix_ro/${i}.mkv" -i "$HOME/ass2/${i}.ass" \
				-map 0:v -vcodec libx265 -metadata:s:v:0 title="第${i}集" \
				-map 0:3 -acodec copy -metadata:s:a:0 title="日语原版" -metadata:s:a:0 language=jpn -disposition:a:0 default \
				-map 1:s -scodec copy -metadata:s:s:0 title="简体中文" -metadata:s:s:0 language=chi -disposition:s:0 default \
				"$prefix_rw/${i}.mkv"
		else
			# 音轨: 2
			batch-task2.py -- ffmpeg -hide_banner \
				-i "$prefix_ro/${i}.mkv" -i "$HOME/ass2/${i}.ass" \
				-map 0:v -vcodec libx265 -metadata:s:v:0 title="第${i}集" \
				-map 0:2 -acodec copy -metadata:s:a:0 title="日语原版" -metadata:s:a:0 language=jpn -disposition:a:0 default \
				-map 1:s -scodec copy -metadata:s:s:0 title="简体中文" -metadata:s:s:0 language=chi -disposition:s:0 default \
				"$prefix_rw/${i}.mkv"

		fi
	fi

}

for i in $(seq -w 55 131)
do

	#if [ -f "~/ass2/${i}.ass" ];then
	#	ls "ass/${i}.ass"
	#	check_audio_jpn "$prefix/${i}.mkv"
	#fi

	echo -n "${i}.mkv 继续执行？{Y/n}" 
	read -n 1 yesno
	echo
	if [ "$yesno"x = yx ] || [ "$yesno"x = x ];then
		new_order_11_08 $i
	else
		echo "先退出"
		exit 0
	fi
	
done
