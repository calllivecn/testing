#!/bin/bash
# date 2024-02-06 21:10:37
# author calllivecn <calllivecn@outlook.com>

# 测试ip 是ipv6 ipv4
test_ip(){
	local PY
PY="\
import ipaddress
ip = ipaddress.ip_address('%s')
print(ip.version)
"
printf "$PY" "$1" |python -
}

# 解析过去30天内，有检测登录的ip. 添加到nft

#journalctl -S "-30 day" -u ssh |grep -oP "Invalid user (.+) from (.+) port" |awk '{print $5}' |sort |uniq -c |awk '{if($1 > 10) print $2}'

for ip in $(journalctl -S "-30 day" -u ssh |grep -oP "Connection closed by Invalid user (.+) (.+) port|Connection closed by authenticating user root (.+) port" |awk '{print $7}' |sort |uniq -c |awk '{if($1 > 10) print $2}')
do

	# 要注意区分ipv4 ipv6
	ip_version=$(test_ip "$ip")

	if [ "$ip_version"x = 4x ];then
		echo "当前ipv4: $ip"
		nft "add element inet netlimit ips { $ip }"
	elif [ $ip_version = 6x ];then
		echo "当前ipv4: $ip"
		nft "add element inet netlimit ip6s { $ip }"
	else
		echo "未知: $ip"
	fi

done

