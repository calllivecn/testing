
# 查看设备有哪些指令
# miiocli chuangmiplug --help

# 查看状态
# miiocli -d -o json_pretty chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN status

# on: 开，off: 关
if [ "$1"x = x ];then
	miiocli chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN status
else
	miiocli chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN "$1"
fi
