
import socket

from pyroute2 import IPRoute

ip = IPRoute()

default_iface = None
default_routes = ip.get_default_routes(family=2)  # IPv4


for route in default_routes:
    oif_index = None
    for attr in route.get("attrs", []):
        if attr[0] == "RTA_OIF":
            oif_index = attr[1]
            break

    if oif_index is not None:
        link_info = ip.get_links(oif_index)[0]
        iface_name = link_info.get_attr("IFLA_IFNAME")
        print(f"默认路由出口接口：{iface_name}")
        default_iface = iface_name


if default_iface:
    print(f"默认 IPv6 出口接口：{default_iface}")

    # 获取该接口所有IPv6地址
    for addr in ip.get_addr(label=default_iface, family=socket.AF_INET6):
        print(f"debug: {addr=}")
        address = addr.get_attr('IFA_ADDRESS')
        flags = addr['flags']  # 直接用 flags 字段
        is_dynamic = bool(flags & 0x02)
        is_mngtmpaddr = bool(flags & 0x100)

        if is_mngtmpaddr:
            print(f"找到 dynamic mngtmpaddr 地址: {address}")
else:
    print("未找到默认 IPv6 出口接口。")

