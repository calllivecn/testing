#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn


import os
import sys
import shutil
import tarfile
from functools import partial

try:
    # import zstd 这个库太简单了，不方便使用
    import pyzstd
    import_zstd = True
except NotImplementedError:
    import_zstd = False


# zstd 的标准压缩块大小是128K , 这里我使用1MB 块
# pyzstd.compress()
BLOCKSIZE = (1<<20)

def read_tar():
    #with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        # shutil.copyfileobj(tar.fileobj, sys.stdout.buffer)

    Zst = pyzstd.ZstdCompressor(level_or_option=10)

    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar, open("/tmp/pax1.tar.zst", "wb") as zst:
        # 这样，需要 输入流 有 readinto() 方法
        # pyzstd.compress_stream(tar, zst, level_or_option=10)

        # for tar_data in iter(partial(tar.fileobj.read, BLOCKSIZE), b""):
        while True:
            tar_data = tar.fileobj.read(BLOCKSIZE)
            if tar_data == b"":
                zst.write(Zst.flush())
                break
            else:
                comp_data = Zst.compress(tar_data)
                zst.write(comp_data)
        

def extract_tar(target):
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, target)
        # tar.list()


def tarextract():
    pass


if __name__ == "__main__":
    # test ok
    read_tar()

    # test ok
    # extract_tar(sys.argv[1]) 
