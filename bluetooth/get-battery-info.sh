#!/bin/bash
# date 2019-12-28 19:43:13
# author calllivecn <c-all@qq.com>

LANG=en

addr2_(){
	echo "$1" |tr ':' '_'
}

get_battery(){
	local mac=$(addr2_ "$1")
	dbus-send --print-reply=literal --system \
		--dest=org.bluez /org/bluez/hci0/dev_${mac} \
		org.freedesktop.DBus.Properties.Get \
		string:"org.bluez.Battery1" string:"Percentage"
}

print_info(){
	local mac=$(addr2_ "$1")
	dbus-send --system --print-reply --dest=org.bluez /org/bluez/hci0/dev_${mac} org.freedesktop.DBus.Introspectable.Introspect
}


if [ -n "$1" ];then
	:
else
	echo "需要蓝牙MAC地址"
	exit 1
fi

print_info "$1"
#get_battery "$1"
