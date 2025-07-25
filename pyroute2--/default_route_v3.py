import socket
from pyroute2 import IPRoute

IFA_F_DYNAMIC = 0x02
IFA_F_TENTATIVE = 0x40
IFA_F_PERMANENT = 0x80
IFA_F_MANAGETEMPADDR = 0x100

ip = IPRoute()

# 先找到默认 IPv6 路由的出口接口 index
default_routes = ip.get_default_routes(family=socket.AF_INET6)
default_oif = None

for route in default_routes:
    for attr in route.get("attrs", []):
        # print(f"Route attr: {attr}")
        if attr[0] == "RTA_OIF":
            default_oif = attr[1]
            break
    if default_oif:
        break

if default_oif is None:
    print("未找到默认 IPv6 路由的出口接口。")
    exit(1)

# 获取接口名
iface_info = ip.get_links(default_oif)[0]
iface_name = iface_info.get_attr("IFLA_IFNAME")
print(f"默认出口接口：{iface_name}")

# 获取该接口上所有 IPv6 地址
addresses = ip.get_addr(index=default_oif, family=socket.AF_INET6)

# 检查是否有带 mngtmpaddr 标志的地址
for addr in addresses:
    ipv6 = addr.get_attr("IFA_ADDRESS")
    #flags = addr.get_attr("flags")
    flags = addr["flags"]
    print(f"IPv6 地址：{ipv6}, flags: {flags:#x}")  # 16 进制输出更方便比对

    is_dynamic = bool(flags & IFA_F_DYNAMIC)
    is_mngtmpaddr = bool(flags & IFA_F_MANAGETEMPADDR)
    is_permanent = bool(flags & IFA_F_PERMANENT)
    is_tentative = bool(flags & IFA_F_TENTATIVE)

    if is_tentative:
        print(f"\t地址 {ipv6} 是 tentative 状态，可能正在进行重复地址检测（DAD）。稍后在试。")
        break

    if is_mngtmpaddr:
        print(f"\t找到符合条件的地址：{ipv6}")

ip.close()

