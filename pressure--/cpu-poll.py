#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-23 15:31:34
# author calllivecn <c-all@qq.com>


"""
解发器写入格式: <some|full> <stall amount in us> <time window in us>
例如，将“some 150000 1000000”写入 /proc/pressure/memory ，表示在1秒内监测到任一任务的内存阻塞超过150毫秒阈值，将会触发唤醒。 将“full 50000 1000000”写入
当前非特权用户也可以创建监视器，唯一的限制是time window必须是2的倍数，以防止过度使用资源。
"""

time_us = 1
time_ms = 1000
time_s = 1000000


import os
import select
import selectors

def test():

    monitor = f"some {100*time_ms} {1*time_s}"

    print(monitor)

    cpu = os.open("/proc/pressure/cpu", os.O_RDWR|os.O_NONBLOCK)

    print(f"{cpu=}, {type(cpu)=}")

    os.write(cpu, monitor.encode())

    poller = select.poll()

    poller.register(cpu, select.POLLIN|select.POLLPRI)

    try:
        while True:
            for fd, event in poller.poll():
                if event & select.POLLIN:
                    data = os.read(fd, 256)
                    print(f'Data is available to read: {data}')
                
                if event & select.POLLPRI:
                    data = os.read(fd, 256)
                    print(f"已经触发发! 可以 read: {data}")

    except KeyboardInterrupt:
        pass

    finally:
        os.close(cpu)


if __name__ == "__main__":
    test()

