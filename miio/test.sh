
# 查看设备有哪些指令
# miiocli chuangmiplug --help

# 查看状态
# miiocli -d -o json_pretty chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN status

# on: 开，off: 关
miiocli -d -o json_pretty chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN off
