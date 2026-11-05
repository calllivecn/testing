#!/usr/bin/env python3
"""
无特权 ICMP ping - 使用 SOCK_DGRAM IPPROTO_ICMP
不需要 root / setcap / cap_net_raw
依赖内核 net.ipv4.ping_group_range 配置
"""

import socket
import struct
import os
import time
import sys
import random
import argparse
import signal


def checksum(data: bytes) -> int:
    """计算 ICMP 校验和（RFC 1071）"""
    if len(data) % 2:
        data += b'\x00'
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + data[i + 1]
        s += w
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def build_icmp_echo(seq: int, payload: bytes = b'') -> bytes:
    """
    构建 ICMP Echo Request 包。
    注意：对于 SOCK_DGRAM IPPROTO_ICMP，内核会接管 id 和 seq 的分配，
    这里填入的值会被内核忽略，但为了包结构的完整性仍需构造。
    """
    icmp_type = 8   # Echo Request
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = 0     # 占位
    icmp_seq = seq  # 占位

    header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    icmp_checksum = checksum(header + payload)
    header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    return header + payload


def build_icmpv6_echo(seq: int, payload: bytes = b'') -> bytes:
    """构建 ICMPv6 Echo Request 包"""
    icmp_type = 128  # ICMPv6 Echo Request
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = 0      # 占位
    icmp_seq = seq   # 占位

    header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    return header + payload


def print_stats(host: str, sent: int, received: int, rtts: list) -> None:
    """打印 ping 统计信息"""
    print(f"\n--- {host} ping statistics ---")
    print(f"{sent} packets transmitted, {received} received, "
          f"{((sent - received) / sent * 100) if sent else 0:.0f}% packet loss")
    if rtts:
        print(f"rtt min/avg/max/mdev = "
              f"{min(rtts):.3f}/{sum(rtts)/len(rtts):.3f}/{max(rtts):.3f}/"
              f"{(sum((x - sum(rtts)/len(rtts))**2 for x in rtts) / len(rtts))**0.5:.3f} ms")


def ping(host: str, count: int = None, timeout: float = 2.0, interval: float = 1.0,
         payload_size: int = 56, force_v4: bool = False, force_v6: bool = False,
         verbose: bool = False, try_all_addrs: bool = False) -> None:
    """
    使用 SOCK_DGRAM IPPROTO_ICMP 发送 ICMP Echo Request
    count=None 表示无限 ping（直到 Ctrl+C）
    """
    # 1. 域名解析
    try:
        addrinfo = socket.getaddrinfo(host, None, socket.AF_UNSPEC, 0, 0)
    except socket.gaierror as e:
        print(f"无法解析主机: {host} ({e})")
        return

    # 2. 提取并去重地址
    ipv4_addrs = []
    ipv6_addrs = []
    for af, _, _, _, addr in addrinfo:
        if af == socket.AF_INET and addr not in ipv4_addrs:
            ipv4_addrs.append(addr)
        elif af == socket.AF_INET6 and addr not in ipv6_addrs:
            ipv6_addrs.append(addr)

    if verbose:
        print("DNS 解析结果:")
        for addr in ipv6_addrs: print(f"  IPv6: {addr}")
        for addr in ipv4_addrs: print(f"  IPv4: {addr}")
        print(f"去重后: IPv4={len(ipv4_addrs)}个, IPv6={len(ipv6_addrs)}个")

    # 3. 决定尝试顺序
    targets = []
    if force_v6:
        targets = [(socket.AF_INET6, socket.IPPROTO_ICMPV6, addr) for addr in ipv6_addrs]
    elif force_v4:
        targets = [(socket.AF_INET, socket.IPPROTO_ICMP, addr) for addr in ipv4_addrs]
    else:
        # 默认 IPv4 优先
        targets = [(socket.AF_INET, socket.IPPROTO_ICMP, addr) for addr in ipv4_addrs] + \
                  [(socket.AF_INET6, socket.IPPROTO_ICMPV6, addr) for addr in ipv6_addrs]

    if not targets:
        print("未找到可用地址")
        return

    if not try_all_addrs:
        targets = [targets[0]]

    print(f"将尝试 {len(targets)} 个地址")

    # 4. 依次尝试 ping
    for af, proto, dst_addr in targets:
        family_name = "ICMPv6" if af == socket.AF_INET6 else "ICMP"
        print(f"\n--- 尝试 {family_name} -> {dst_addr[0]} ---")

        try:
            sock = socket.socket(af, socket.SOCK_DGRAM, proto)
        except PermissionError:
            print("创建 ICMP socket 被拒绝，请检查 ping_group_range")
            continue
        except OSError as e:
            print(f"创建 socket 失败: {e}")
            continue

        sock.settimeout(timeout)
        payload = bytes(random.getrandbits(8) for _ in range(payload_size))
        print(f"PING {host} ({dst_addr[0]}) {payload_size} data bytes")

        sent = 0
        received = 0
        rtts = []
        actual_id = None
        interrupted = False

        def handle_interrupt(signum, frame):
            nonlocal interrupted
            interrupted = True

        old_handler = signal.signal(signal.SIGINT, handle_interrupt)

        try:
            seq = 1
            while True:
                # 检查是否达到发包数上限
                if count is not None and seq > count:
                    break

                pkt = build_icmp_echo(seq, payload) if af == socket.AF_INET else build_icmpv6_echo(seq, payload)
                try:
                    t0 = time.monotonic()
                    sock.sendto(pkt, (dst_addr[0], 0))
                    sent += 1
                    if verbose: print(f"  seq={seq} 已发送 ({len(pkt)} bytes)")
                except OSError as e:
                    print(f"seq={seq} 发送失败: {e}")
                    time.sleep(interval)
                    seq += 1
                    continue

                try:
                    while True:
                        data, addr = sock.recvfrom(4096)
                        t1 = time.monotonic()
                        rtt_ms = (t1 - t0) * 1000

                        if len(data) < 8: continue
                        r_type, r_code, r_cksum, r_id, r_seq = struct.unpack('!BBHHH', data[:8])

                        if actual_id is None:
                            actual_id = r_id
                            if verbose: print(f"  [内核分配 id={actual_id}]")

                        is_echo_reply = (r_type == 0 and af == socket.AF_INET) or \
                                        (r_type == 129 and af == socket.AF_INET6)

                        if is_echo_reply and r_id == actual_id and r_seq == seq:
                            received += 1
                            rtts.append(rtt_ms)
                            print(f"{len(data)} bytes from {dst_addr[0]}: icmp_seq={r_seq} ttl=64 time={rtt_ms:.1f} ms")
                            break
                        elif verbose:
                            print(f"  [recv] 忽略: type={r_type} id={r_id} seq={r_seq} (期望 id={actual_id} seq={seq})")
                except socket.timeout:
                    print(f"seq={seq} 超时")

                if interrupted:
                    print("\n^C")
                    break

                seq += 1
                if count is None or seq <= count:
                    time.sleep(interval)

        finally:
            signal.signal(signal.SIGINT, old_handler)
            sock.close()

        if received > 0 or interrupted:
            print_stats(host, sent, received, rtts)
            return
        else:
            print("当前地址不可达，尝试下一个...")

    print("所有尝试的地址均不可达")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="无特权 ICMP Ping")
    parser.add_argument("host", help="目标主机或 IP")
    parser.add_argument("-c", type=int, default=None, help="发包数（默认无限，直到 Ctrl+C）")
    parser.add_argument("-W", type=float, default=2.0, help="超时(秒)")
    parser.add_argument("-i", type=float, default=1.0, help="间隔(秒)")
    parser.add_argument("-s", type=int, default=56, help="载荷大小")
    parser.add_argument("-4", action="store_true", help="强制 IPv4")
    parser.add_argument("-6", action="store_true", help="强制 IPv6")
    parser.add_argument("-v", action="store_true", help="详细模式")
    parser.add_argument("-a", action="store_true", help="尝试所有 DNS 解析地址")
    args = parser.parse_args()

    ping(args.host, count=args.c, timeout=args.W, interval=args.i,
         payload_size=args.s, force_v4=args.__dict__['4'], force_v6=args.__dict__['6'],
         verbose=args.v, try_all_addrs=args.a)
