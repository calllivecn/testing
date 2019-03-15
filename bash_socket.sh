#!/bin/bash
# date 2018-04-05 02:04:34
# author calllivecn <c-all@qq.com>



go(){

while :
do
	echo -n "继续下一个例子？[Y/n]: "
	read -n 1 y;
	y=${y:-yes}
	echo
	if [ "$y"x = yx ];then
		:
		return 0
	elif [ "$y"x = nx ];then
		echo "exit..."
		exit 0
	else
		continue
	fi
done
}

# 在bash下，你可以打开一个套接字并通过它发送数据。你不必使用 curl 或者 lynx 命令抓取远程服务器的数据。bash 和两个特殊的设备文件可用于打开网络套接字。以下选自 bash 手册：
#
# /dev/tcp/host/port - 如果 host 是一个有效的主机名或者网络地址，而且端口是一个整数或者服务名，bash 会尝试打开一个相应的 TCP 连接套接字。
# /dev/udp/host/port - 如果 host 是一个有效的主机名或者网络地址，而且端口是一个整数或者服务名，bash 会尝试打开一个相应的 UDP 连接套接字。

# 打开，关闭socket: exec $fd<>/dev/tcp/host/port; exec $fd<&-;

# 你可以使用这项技术来确定本地或远程服务器端口是打开或者关闭状态，而无需使用 nmap 或者其它的端口扫描器。

for p in {1..1023}
do
	(echo >/dev/tcp/localhost/$p) >/dev/null 2>&1 && echo "$p open"
done

go

# 下面的示例中，你的 bash 脚本将像 HTTP 客户端一样工作：

exec 3<> /dev/tcp/${1:-www.cyberciti.biz}/80
printf "GET / HTTP/1.0\r\n" >&3
printf "Accept: text/html, text/plain\r\n" >&3
printf "Accept-Language: en\r\n" >&3
printf "User-Agent: nixCraft_BashScript v.%s\r\n" "${BASH_VERSION}"   >&3
printf "\r\n" >&3

while read LINE <&3
do
   # do something on $LINE
   # or send $LINE to grep or awk for grabbing data
   # or simply display back data with echo command
   echo $LINE
done
