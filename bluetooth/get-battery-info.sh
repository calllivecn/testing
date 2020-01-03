#!/bin/bash
# date 2019-12-28 19:43:13
# author calllivecn <c-all@qq.com>

LANG=en

#dbus-send --print-reply=literal --system \
#	--dest=org.bluez /org/bluez/hci0/dev_E4_08_BD_67_04_9A \
#	org.freedesktop.DBus.Properties.Get \
#	string:"org.bluez.Battery1" string:"Percentage"

dbus-send --system --print-reply --dest=org.bluez /org/bluez/hci0/dev_E4_08_BD_67_04_9A org.freedesktop.DBus.Introspectable.Introspect
