#!/usr/bin/env python3
# coding=utf-8
# date 2022-08-18 23:43:43
# author calllivecn <calllivecn@outlook.com>

"""
使用pyzstd 继承 tarfile 的方法来使用
"""

import os
import sys
import tarfile

from pyzstd import (
    ZstdFile,
    CParameter,
)

def cpu_physical():
    with open("/proc/cpuinfo") as f:
        while (line := f.readline()) != "":
            if "cpu cores" in line:
                count = line.strip("\n")
                break

    _, cores = count.split(":")
    return int(cores.strip())


# 直接继承 TarFile 类; 我需要 支持其他解压方法和输出到标准输出，可以好像不能使用这种方法？
class ZstdTarFile(tarfile.TarFile):
    def __init__(self, name, mode='r', *, level_or_option=None, zstd_dict=None, **kwargs):
        self.zstd_file = ZstdFile(name, mode,
                                  level_or_option=level_or_option,
                                  zstd_dict=zstd_dict)
        try:
            super().__init__(fileobj=self.zstd_file, mode=mode, **kwargs)
        except:
            self.zstd_file.close()
            raise

    def close(self):
        try:
            super().close()
        finally:
            self.zstd_file.close()


# write .tar.zst file (compression)
def maketar(archive, target, level=5, threads=cpu_physical()):
    op = {
        CParameter.compressionLevel: level,
        CParameter.nbWorkers: threads
    }
    with ZstdTarFile(archive, mode='w', level_or_option=op) as tar:
        tar.add(target)

# read .tar.zst file (decompression)
def extracttar(archive, target):
    with ZstdTarFile(archive, mode='r') as tar:
        tar.extractall(target)


if __name__ == "__main__":
    if sys.argv[1] == "c":
        maketar(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "x":
        extracttar(sys.argv[2], sys.argv[3])