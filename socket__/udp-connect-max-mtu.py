#!/usr/bin/env python3
# coding=utf-8
# date 2022-05-09 00:02:39
# author calllivecn <c-all@qq.com>

"""
#define IP_PMTUDISC_DONT   0    /* Never send DF frames.  */
#define IP_PMTUDISC_WANT   1    /* Use per route hints.  */
#define IP_PMTUDISC_DO     2    /* Always DF.  */
#define IP_PMTUDISC_PROBE  3    /* Ignore dst pmtu.  */
"""

__author__ = 'SunQi 2012210465 '

import sys
import socket
import struct
import os
import array
import string
import select
import getopt

ICMP_TYPE = 8
ICMP_TYPE_IP6 = 128
ICMP_CODE = 0
ICMP_CHECKSUM = 0
ICMP_ID = 0
ICMP_SEQ_NR = 0
IP_MTU_DISCOVER = 10
IP_PMTUDISC_DONT = 0
IP_PMTUDISC_DO = 2
mid = 0


def _in_cksum(packet):
    if len(packet) & 1:
        packet += '\0'
    words = array.array('h', packet)
    chksums = 0
    for word in words:
        chksums += (word & 0xffff)
    hi = chksums >> 16
    lo = chksums & 0xffff
    chksums = hi + lo
    chksums += chksums >> 16
    return (~chksums) & 0xffff


def _search(size, pong, mid):
    if not (1472 >= size >= 548):
        print("illegal size option")

    while 1:
        pong = pingNode(alive=alive, timeout=timeout, number=count, node=node)
        if not pong:
            mid = (size - 548) // 2
            size -= mid
            print("dead")
            print(mid, size)
            return size, mid
        else:
            print("live")
            if mid == 0:
                size += 1

        mid //= 2
        size += mid
        print(mid, size)
        return size, mid


def _error(err):
    if __name__ == '__main__':
        print(f"{os.path.basename(sys.argv[0])}: {str(err)}")
        print(f"Try `{os.path.basename(sys.argv[0])} --help' for more information.")
        sys.exit(1)
    else:
        raise Exception(str(err))


def construct(sid, size):
    data = ""
    data += size * "X"
    header = struct.pack('bbHHh', ICMP_TYPE, ICMP_CODE, ICMP_CHECKSUM,
                         ICMP_ID, ICMP_SEQ_NR + sid)
    packet = header + data
    checksum = _in_cksum(packet)
    header = struct.pack('bbHHh', ICMP_TYPE, ICMP_CODE, checksum, ICMP_ID,
                         ICMP_SEQ_NR + sid)
    packet = header + data
    return packet


def pingNode(alive=0, timeout=1.0, number=sys.maxsize, node=None, size=1472):
    dst_ip = socket.gethostbyname(node)
    test_mid = 0
    if not node:
        _error("")
    try:
        host = socket.gethostbyname(node)
    except:
        _error("cannot resolve %s: Unknown host" % node)
    if int(string.split(dst_ip, ".")[-1]) == 0:
        _error("no support for network ping")
    if number == 0:
        _error("invalid count of packets to transmit")
    if alive:
        number = 1
    start = 1

    lost = 0

    if not alive:
        print(f"PING {str(node)} ({str(dst_ip)}): {20 + 8 + size} data bytes (20+8+{size})")

    try:
        while start <= number:
            try:
                pingSocket = socket.socket(socket.AF_INET, socket.IPPROTO_ICMP)
                pingSocket.setsockopt(socket.SOL_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)
            except socket.error as e:
                print("socket error: %s" % e)
                _error("You must be root (%s uses raw sockets)" % os.path.basename(sys.argv[0]))

            packet = construct(start, size)
            try:
                pingSocket.sendto(packet, (node, 1))
            except socket.error as e:
                _error("socket error: %s" % e)

            pong = 0
            if size + 28 <= 748:
                    pong = "1"
            """
            iwtd = []
            while 1:
                iwtd, owtd, ewtd = select.select([pingSocket], [], [], timeout)
                break
            if iwtd:
                pong, address = pingSocket.recvfrom(size + 48)
                lost -= 1

                pongHeader = pong[20:28]
                pongType, pongCode, pongChksum, pongID, pongSeqnr = \
                    struct.unpack("bbHHh", pongHeader)

                if not pongSeqnr == start:
                    pong = None

            if not pong:
                if alive:
                    print "no reply from %s (%s)" % (str(node), str(host))
                else:
                    print "ping timeout: %s (icmp_seq=%d) " % (host, start)
                    print "Current mtu is %d" % (size + 28)
                    size, test_mid = _search(size, pong, mid)
                    start += 1
                continue

            size, test_mid = _search(size, pong, test_mid)
            """
    except (EOFError, KeyboardInterrupt):
        start += 1
        pass
    return pong
    pingSocket.close()


def _usage():
    e="""link mtu finder
    python ping.py <ip_address>
    """
    print(e)


if __name__ == "__main__":
    """
    Main loop
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:-1], "hat:6c:fs:")
    except getopt.GetoptError:
        _error("fucking illegal option")

    if len(sys.argv) >= 2:
        node = sys.argv[-1:][0]
        if node[0] == '-':
            _usage()
    else:
        _error("No arguments given")

    if args:
        _error("illegal option -- %s" % str(args))
    alive = 0
    timeout = 1.0
    count = sys.maxsize
    flood = 0

    sys.exit()
