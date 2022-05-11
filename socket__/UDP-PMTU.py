#!/usr/bin/env python3
# coding=utf-8
# date 2022-05-10 20:30:57
# author calllivecn <c-all@qq.com>

"""
使用二分法测试链路上，最大UDP MTU.
"""

"""
查看发送缓冲区大小
udp.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)

查看接收缓冲区大小
udp.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)


ipv6 与 IPv4 相比，路由器不会对大于最大传输单元(MTU) 的 IPv6 数据包进行分段，这是始发节点的唯一责任。IPv6 要求最小 MTU 为 1,280个八位字节，但“强烈建议”主机使用路径 MTU 发现以利用大于最小值的 MTU。

"""

import sys
import ssl
import time
import socket
import argparse


# init RTT  还是叫 RTO ?
RTT=5
RTT_COUNT=3

def wrap_rtt(func):
    def wrap(*args, **kwarg):
        global RTT
        t1 = time.time()
        result = func(*args, **kwarg)
        t2 = time.time()

        e = t2-t1
        if result:
            RTT = e*2
            if RTT > 30:
                RTT=30
        else:
            RTT = e*1.1


        return result
    
    return wrap



@wrap_rtt
def pmtud(sock, MSS_try):
    # sock.send(bytes(MSS_try))
    sock.send(ssl.RAND_bytes(MSS_try))
    try:
        data, addr = sock.recvfrom(1024)
    except Exception:
        return False
    
    return True


def client(args, sock):

    if args.target is None:
        print("需要目标地址")
        sys.exit(1)

    HOST = args.target               # Symbolic name meaning all available interfaces
    PORT = args.port                     # Arbitrary non-privileged port



    lo = args.min
    hi = args.max

    print(f'>>> UDP PMTU 探测目标：{args.target} 范围 [{lo}, {hi})')

    sock.connect((HOST, PORT))
    sock.settimeout(args.timeout)

    mid = lo
    while lo+1 < hi:

        print(f"负载 {mid}: ", end="", flush=True)

        udp_ok = True
        for i in range(args.retry):
            if pmtud(sock, mid):
                print('ok', flush=True)
                udp_ok = True
                break
            else:
                print('* ', end="", flush=True)
                time.sleep(args.interval)
                udp_ok = False
                
            
        if udp_ok:
            lo = mid
        else:
            # all attempts failed, payload probably too big
            hi = mid
            print(flush=True)

        mid = (lo + hi + 1) // 2
        
        # set RTT 为 timeout
        sock.settimeout(RTT)

    # header_size = 28 if args.ipv4 else 48
    if sock.family == socket.AF_INET:
        header = 28
        print(f">>> IPv4 MTU to {args.target}: {lo} + {header} = {lo+header}")
    else:
        header = 48
        print(f">>> IPv6 MTU to {args.target}: {lo} + {header} = {lo+header}")
    
    sock.close()

def server(port):
    BUF=32*(1<<10) # 32K
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(("", port))

    while True:
        data, addr = sock.recvfrom(BUF)
        size = len(data)
        print(f"{addr}: UPD packet size:{size}")
        sock.sendto(str(size).encode("utf8"), addr)


def main():

    parse = argparse.ArgumentParser(description='使用 UDP 探测 MTU')

    parse.add_argument('target', nargs="?", help='IP address or hostname (兼容ipv4 ipv6)')

    # group = parse.add_mutually_exclusive_group()
    # group.add_argument('--ipv4', '-4', action='store_true', help='use IPv4')
    # group.add_argument('--ipv6', '-6', action='store_true', help='use IPv6')

    parse.add_argument('--server', action="store_true", help='服务端 (default: 客户端)')
    parse.add_argument('--port', type=int, default=6789, help='端口 [%(default)s]')

    # 68 or 576 for IPv4, 1280 for IPv6
    parse.add_argument('-l', metavar='MTU min', dest='min', type=int, default=512, help=f'探测起始包大小 ipv4:576-28=548, ipv6:1280-48=1232')
    parse.add_argument('-u', metavar='MTU max', dest='max', type=int, default=1500, help='探测结束包大小 ipv6: 目前实测一般很大，万级。 [default:%(default)s]')
    parse.add_argument('-c', metavar='COUNT', dest='retry', type=int, default=2, help='最大重试次数 [default:%(default)s]')
    parse.add_argument('-w', metavar='SECONDS', dest='timeout', type=float, default=2, help='首次探测的超时时间 [default:%(default)s]')
    parse.add_argument('-i', metavar='SECONDS', dest='interval', type=float, default=0.2, help='探测包的发送间隔 [default%(default)s]')

    args = parse.parse_args()

    # 自动检测是ipv4 ipv6
    sock = None
    for res in socket.getaddrinfo(args.target, args.port, socket.AF_UNSPEC, socket.SOCK_DGRAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:
            sock = socket.socket(af, socktype, proto)
        except OSError as msg:
            sock = None
            continue

        break

    if sock is None:
        print('could not open socket')
        sys.exit(1)

    if args.server:
        server(args.port)
    else:
        client(args, sock)


if __name__ == "__main__":
    main()