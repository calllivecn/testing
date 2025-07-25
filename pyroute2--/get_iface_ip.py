
import sys
#import socket

from pyroute2 import IPRoute

ip = IPRoute()

default_iface = sys.argv[1]  # IPv4: 2, ipv6: 10


if default_iface:
    print(f"默认 IPv6 出口接口：{default_iface}")

    iface_info: list = ip.get_addr(label=default_iface)
    #index = iface_info[0].get_attr("IFA_LABEL")
    index = iface_info[0]["index"]

    # 获取该接口所有IPv6地址
    for addr in ip.get_addr(index=index, family=10):
        ipv6 = addr.get_attr('IFA_ADDRESS')
        flags = addr['flags']  # 直接用 flags 字段

        print(f"IPv6 地址：{ipv6}, flags: {flags:#x}")  # 16 进制输出更方便比对

        is_dynamic = bool(flags & 0x02)
        is_mngtmpaddr = bool(flags & 0x100)
        is_permanent = bool(flags & 0x80)

        if is_mngtmpaddr:
            print(f"找到mngtmpaddr 地址: {ipv6}")
        if is_permanent:
            print(f"找到permanent 地址: {ipv6}")
else:
    print("未找到默认 IPv6 出口接口。")

