#!/usr/bin/env python3
# coding=utf-8
"""
IPv6 UDP PMTU 探测（内核 PTB 直读版）。

不再依赖应用层回显和二分查找，而是启用 IPV6_RECVPATHMTU，
让内核把 ICMPv6 Packet Too Big 中的精确 MTU 直接交给应用。
"""

import sys
import ssl
import time
import socket
import struct
import argparse
import errno

# Linux 上 ip6_mtuinfo 通常为 32 字节，ip6m_mtu 位于偏移 28，主机字节序
IP6_MTUINFO_LEN = 32
IP6M_MTU_OFFSET = 28

IPV6_RECVPATHMTU = getattr(socket, "IPV6_RECVPATHMTU", 60)
IPV6_DONTFRAG = getattr(socket, "IPV6_DONTFRAG", 62)
IPV6_PATHMTU = getattr(socket, "IPV6_PATHMTU", 61)
IPV6_MTU = getattr(socket, "IPV6_MTU", 24)


def configure_socket(sock, timeout):
    """启用 PMTU 通知，禁止本地分片，让内核直接报告精确 MTU。"""
    sock.setsockopt(socket.IPPROTO_IPV6, IPV6_RECVPATHMTU, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, IPV6_DONTFRAG, 1)
    sock.settimeout(timeout)


def send_probe(sock, payload_size):
    """
    发送一个探测包。
    返回 (status, pmtu)：
      status == "ok"        : 发送成功，路径 MTU >= 该 payload
      status == "toobig"    : 内核报告 EMSGSIZE，pmtu 为精确值
      status == "timeout"   : 超时或其他错误，本次结果不可靠
    """
    data = ssl.RAND_bytes(payload_size)
    try:
        sock.send(data)
        return "ok", None
    except OSError as e:
        if e.errno == errno.EMSGSIZE:
            # 对于已 connect 的 UDP socket，Linux 会在此处暴露更新后的 PMTU
            pmtu = sock.getsockopt(socket.IPPROTO_IPV6, IPV6_MTU)
            return "toobig", pmtu
        elif e.errno in (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
            return "timeout", None
        else:
            return "error", e


def receive_with_pmtu(sock, bufsize=4096):
    """
    接收普通 UDP 数据，或捕获内核投递的 IPV6_PATHMTU 辅助数据。
    返回 (data, addr, pmtu_or_None)。
    """
    ancbufsize = socket.CMSG_SPACE(IP6_MTUINFO_LEN)
    try:
        data, ancdata, flags, addr = sock.recvmsg(bufsize, ancbufsize)
    except socket.timeout:
        return b"", None, None

    new_pmtu = None
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == socket.IPPROTO_IPV6 and cmsg_type == IPV6_PATHMTU:
            if len(cmsg_data) >= IP6_MTUINFO_LEN:
                new_pmtu = struct.unpack_from("=I", cmsg_data, IP6M_MTU_OFFSET)[0]
    return data, addr, new_pmtu


def probe_pmtu(sock, lo, hi, interval):
    """
    利用内核 PTB 信息探测路径 MTU。
    不再使用“失败即收缩上界”的二分法，而是：
      - 发送成功 → 下界上移
      - 收到 EMSGSIZE → 内核直接给出精确 PMTU，立即返回
      - 超时 → 跳过该 size，不污染搜索空间
    """
    last_ok = lo

    while lo <= hi:
        mid = (lo + hi) // 2
        print(f"尝试负载 {mid}: ", end="", flush=True)

        status, pmtu = send_probe(sock, mid)

        if status == "ok":
            print("ok（路径 MTU ≥ 该值）")
            last_ok = mid
            lo = mid + 1

        elif status == "toobig":
            print(f"EMSGSIZE，内核报告 PMTU = {pmtu}")
            # 内核已经给出精确 PMTU，payload 上界 = PMTU - 48（IPv6 头 + UDP 头）
            payload_limit = pmtu - 48
            print(f">>> 精确路径 MTU: {pmtu}（对应最大负载约 {payload_limit} 字节）")
            return pmtu, payload_limit

        elif status == "timeout":
            print("超时（结果不可靠，跳过该点）")
            # 关键改动：超时不收缩上界，只跳过当前 mid
            lo = mid + 1

        else:
            print(f"发送错误: {pmtu}")
            lo = mid + 1

        time.sleep(interval)

    print(f">>> 未收到 PTB，探测区间内最小成功负载为 {last_ok}，实际 MTU 可能 ≥ {last_ok + 48}")
    return None, last_ok


def client(args, sock):
    if args.target is None:
        print("需要目标地址")
        sys.exit(1)

    sock.connect((args.target, args.port))
    configure_socket(sock, args.timeout)

    print(f">>> IPv6 PMTU 探测目标：{args.target}  负载范围 [{args.min}, {args.max}]")
    print(">>> 已启用 IPV6_RECVPATHMTU / IPV6_DONTFRAG，PTB 由内核直读\n")

    pmtu, payload_limit = probe_pmtu(sock, args.min, args.max, args.interval)

    # 无论 send 是否触发 EMSGSIZE，都尝试从内核读取当前 PMTU
    if pmtu is None:
        try:
            pmtu = sock.getsockopt(socket.IPPROTO_IPV6, IPV6_MTU)
            print(f"\n>>> 内核当前缓存的 IPV6_MTU: {pmtu}")
        except OSError:
            pmtu = None

    if pmtu:
        print(f">>> 最终结果：路径 MTU = {pmtu} 字节（IPv6 头 40 + UDP 头 8 + 负载 {pmtu - 48}）")
    else:
        print(f">>> 最终结果：仅能确认负载 {payload_limit} 可通，未获取到精确 PTB")

    sock.close()


def server(port):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(("::", port))
    print(f"listen port: {port} (IPv6)")

    while True:
        data, addr = sock.recvfrom(65535)
        print(f"{addr}: UDP packet size: {len(data)}")
        sock.sendto(str(len(data)).encode(), addr)


def main():
    parse = argparse.ArgumentParser(description="IPv6 UDP PMTU 探测（内核 PTB 直读）")
    parse.add_argument("target", nargs="?", help="IPv6 地址或主机名")
    parse.add_argument("--server", action="store_true", help="服务端模式")
    parse.add_argument("--port", type=int, default=6789, help="端口 [%(default)s]")
    parse.add_argument("-l", dest="min", type=int, default=512, help="起始负载 [%(default)s]")
    parse.add_argument("-u", dest="max", type=int, default=2000, help="最大负载 [%(default)s]")
    parse.add_argument("-w", dest="timeout", type=float, default=2, help="超时秒数 [%(default)s]")
    parse.add_argument("-i", dest="interval", type=float, default=0.3, help="探测间隔 [%(default)s]")

    args = parse.parse_args()

    if args.server:
        server(args.port)
        return

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    client(args, sock)


if __name__ == "__main__":
    main()
