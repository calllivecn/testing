

for mp4 in *.mp4
do
	INFO=$(ffprobe -hide_banner -show_streams -print_format json ${mp4} 2>/dev/null)
	echo ${INFO} |jsonfmt.py -d streams.[0].codec_name
	echo ${INFO} |jsonfmt.py -d streams.[0].width
	echo ${INFO} |jsonfmt.py -d streams.[0].height
	echo ${INFO} |jsonfmt.py -d streams.[1].codec_name
done
