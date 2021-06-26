#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn


import os
import sys
import shutil
import tarfile

try:
    import zstd
except NotImplementedError:
    print("pip install zstd", file=sys.stderr)
    sys.exti(1)

# def read_tar(archivename):
def read_tar():
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        shutil.copyfileobj(tar.fileobj, sys.stdout.buffer)


def extract_tar(target):
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        tar.extractall(target)
        # tar.list()


# zstd 的标准压缩块大小是128K , 这里我使用1MB 块
# zstd.compress()



def main():
    import argparse

    parse = argparse.ArgumentParser(
        description="like GNU tar",
        usage="%(prog)s [option] [file ...]",
        epilog="https://github.com/calllivecn/mytools"
        )
    
    parse.add_argument("-f", help="tar 文件")
    parse.add_argument("-x", help="解压")
    parse.add_argument("-C", help="解压到指定目录(default: 当前目录)")
    parse.add_argument("-z", help="使用压缩，zstd，default: level=11")
    parse.add_argument("-l", help="使用压缩level=11，level: 1 ~ 22")
    parse.add_argument("-e", help="使用 aes 加密")

    # 从标准输入赢取
    parse.add_argument("--stdin", help="从标准输入读取")
    parse.add_argument("--stdout", help="输出到标准输出")




if __name__ == "__main__":
    # test ok
    # read_tar()

    # test ok
    # extract_tar(sys.argv[1]) 
    
    main()

