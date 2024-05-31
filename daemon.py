

import os
import sys
import time
import subprocess

"""
这样测试可以的

"""

def func():
    while True:
        print(".", end="")
        time.sleep(1)

def daemonize():
    """
    将进程转换为守护进程。
    """
    # 创建子进程。
    pid = os.fork()
    if pid == 0:
        func()
    else:
        # 父进程。
        sys.exit(0)

if __name__ == '__main__':
    daemonize()

