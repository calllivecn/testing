#!/usr/bin/env python3
# coding=utf-8
# date 2022-05-09 00:10:46
# author calllivecn <c-all@qq.com>

import time
import socket
import argparse
import subprocess

def ping_works(payload_size, args):
    # we capture the output to prevent ping
    # from printing to terminal
    output = subprocess.run([
        'ping',
        '-4' if args.ipv4 else '-6',
        '-M', 'do',
        '-c', '1',
        '-w', str(args.step_timeout_sec),
        '-n',
        '-s', str(payload_size),
        args.target,
    ], capture_output=True)
    # , check=True) 

    if output.returncode == 0:
        return True
    else:
        return False

def main(args):
    lo = args.lo  # MTUs lower or equal do work
    hi = args.hi  # MTUs greater or equal don't work
    print(f'>>> PMTU to {args.target} in range [{lo}, {hi})')

    while lo + 1 < hi:
        mid = (lo + hi) // 2

        print(f"{mid}: ", end="", flush=True)

        for i in range(args.max_pings_per_step):
            if ping_works(mid, args):
                # ping went through, this payload size works
                lo = mid
                print('pong', flush=True)
                break
            else:
                print('* ', end="", flush=True)
                time.sleep(args.ping_interval_sec)
        else:
            # all attempts failed, payload probably too big
            hi = mid
            print(flush=True)

    header_size = 28 if args.ipv4 else 48
    print(f">>> optimal MTU to {args.target}: {lo} + {header_size} = {lo+header_size}")

def parse_args():
    p = argparse.ArgumentParser(description='Perform path MTU discovery.')

    p.add_argument('target', help='IP address or hostname to ping')

    group = p.add_mutually_exclusive_group()
    group.add_argument('--ipv4', '-4', action='store_true', help='use IPv4')
    group.add_argument('--ipv6', '-6', action='store_true', help='use IPv6')

    # 68 or 576 for IPv4, 1280 for IPv6
    p.add_argument('-l', metavar='MTU', dest='lo', type=int, default=576, help='lower bound of the search range [%(default)s]')
    p.add_argument('-u', metavar='MTU', dest='hi', type=int, default=1500, help='upper bound of the search range [%(default)s]')
    p.add_argument('-c', metavar='COUNT', dest='max_pings_per_step', type=int, default=2, help='maximum number of pings per step [%(default)s]')
    p.add_argument('-w', metavar='SECONDS', dest='step_timeout_sec', type=int, default=2, help='step timeout [%(default)s]')
    p.add_argument('-i', metavar='SECONDS', dest='ping_interval_sec', type=float, default=0.2, help='ping interval [%(default)s]')

    args = p.parse_args()

    addrinfo = socket.getaddrinfo(args.target, 0, socket.AF_UNSPEC, socket.SOCK_DGRAM)

    if args.ipv4:
        addrinfo = [_ for _ in addrinfo if _[0] == socket.AF_INET]
        if not addrinfo:
            p.error('target has no IPv4 address')

    if args.ipv6:
        addrinfo = [_ for _ in addrinfo if _[0] == socket.AF_INET6]
        if not addrinfo:
            p.error('target has no IPv6 address')

    for af, socktype, proto, _, sockaddr in addrinfo:
        try:
            # check route to the host using UDP connect()
            s = socket.socket(af, socktype, proto)
            s.connect(sockaddr)
            s.close()
            break
        except Exception:
            pass
    else:
        p.error('no routes to target')

    args.ipv4 = (af == socket.AF_INET)
    args.ipv6 = (af == socket.AF_INET6)
    args.target = sockaddr[0]

    return args

if __name__ == '__main__':
    main(parse_args())
