#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn


import io
import os
import re
import sys
import glob
import shutil
import tarfile
import pathlib
import threading
from pathlib import Path
from fnmatch import fnmatchcase


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

    Zst = pyzstd.ZstdCompressor(level_or_option=7)

    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar, open("/tmp/pax1.tar.zst", "wb") as zst:
        # 这样，需要 输入流 有 readinto() 方法
        # pyzstd.compress_stream(tar, zst, level_or_option=10)

        while (tar_data := tar.fileobj.read(BLOCKSIZE)) != b"":
            comp_data = Zst.compress(tar_data)
            zst.write(comp_data)

        zst.write(Zst.flush())
        

def extract_tar(target):
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        tar.extractall(target)
        # tar.list()


def tarextract():
    pass


# 测试使用os.pipe管道， 连接 tar | zstd | crypto | split
# 这里先测试 tar | zstd

# tarfile.open() 需要 fileobj 需要包装一下。
# pipe 是两个FD 需要 关闭两次, 写关闭时: read() -> b""
class Pipe:

    def __init__(self):
        self.r, self.w = os.pipe()
    
    def read(self, size):
        return os.read(self.r, size)

    def write(self, data):
        return os.write(self.w, data)
    
    def close(self):
        os.close(self.r)
        os.close(self.w)


# 需要先定义 zstd 处理函数，以启动线程处理。

def tar2pipe(path, pipe, filter=None):
    with tarfile.open(mode="w|", fileobj=pipe) as tar:
        tar.add(path, filter=filter)

    pipe.close()
    print("tar make done")

def pipe2tar(pipe, path, filter=None):
    with tarfile.open(mode="r|", fileobj=pipe) as tar:
        tar.extractall(path)
    
    print("tar extract done")

def compress(pipe, w):
    op = {
        # pyzstd.CParameter.nbWorkers: os.cpu_count(),
        pyzstd.CParameter.nbWorkers: 8,
        pyzstd.CParameter.compressionLevel: 19
    }
    zst = pyzstd.ZstdCompressor(op)
    while (data := pipe.read(BLOCKSIZE)) != b"":
        comp_data = zst.compress(data)
        w.write(comp_data)
    
    w.write(zst.flush())
    pipe.close()

    print("compress done")

def decompress(r, pipe):
    zst = pyzstd.ZstdDecompressor()
    while (data := r.read(BLOCKSIZE)) != b"":
        pipe.write(zst.decompress(data))

    pipe.close()
    print("decompress done")


def maketar(archive, path):
    pipe = Pipe()
    # pipe = Pipe2()
    print(pipe.r, pipe.w)
    with open(archive, "wb") as zst:

        tar_th = threading.Thread(target=tar2pipe, args=(path, pipe), daemon=True)
        tar_th.start()

        zst_th = threading.Thread(target=compress, args=(pipe, zst), daemon=True)
        zst_th.start()

        tar_th.join()
        zst_th.join()

        pipe.close2()

    print("done")


def extract_tar(archive, path):
    pipe = Pipe()
    # pipe = Pipe2()
    print(pipe.r, pipe.w)
    with open(archive, "rb") as zst:

        tar_th = threading.Thread(target=pipe2tar, args=(pipe, path), daemon=True)
        tar_th.start()

        zst_th = threading.Thread(target=decompress, args=(zst, pipe), daemon=True)
        zst_th.start()

        tar_th.join()
        zst_th.join()

        pipe.close2()

    print("done")



def test1():
    # test ok
    # read_tar()

    # test ok
    extract_tar(sys.argv[1]) 


def test2():
    # test pipe ok
    if sys.argv[1] == "c":
        maketar(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "x":
        extract_tar(sys.argv[2], sys.argv[3])
    else:
        print("Usage: <c|x> <archive> <target>")

# 用户过滤参数转为 list
def exclude(ls):
    return [ re.compile(l) for l in ls]

# 测试过滤
def filter1(tarinfo, fs):
    for ref in fs:
        if ref.match(tarinfo.name):
            print("过滤：", tarinfo.name)
            return None
    else:
        print("打包：", tarinfo.name)
        return tarinfo

def filter2(tarinfo, fs, verbose):
    for fm in fs:
        if fnmatchcase(tarinfo.name, fm):
            return None
    else:
        if verbose:
            print(tarinfo.name, file=sys.stderr)
        return tarinfo


def maketar(archive, path, verbose, excludes=[]):
    """
    处理打包路径安全:
    只使用 给出路径最右侧做为要打包的内容
    例："../../dir1/dir2" --> 只会打包 dir2 目录|文件
    """
    p = Path(path)
    abspath = p.resolve()
    arcname = abspath.relative_to(abspath.parent)

    # ls = exclude(fs)

    with tarfile.open(archive, mode="w") as tar:
        # tar.add(p, arcname)
        tar.add(p, arcname, filter=lambda x: filter2(x, excludes, verbose))


def order_bad_path(tarinfo):
    """
    处理掉不安全 tar 成员路径(这样有可能会产生冲突而覆盖文件):
    ../../dir1/file1 --> dir1/file1
    注意：使用 Path() 包装过的路径，只会剩下左边的"../"; 所有可以这样处理。
    """
    path = pathlib.Path(tarinfo.name)
    cwd = pathlib.Path()
    for part in path.parts:
        if part == "..":
            continue
        else:
            cwd = cwd / part

    tarinfo.name = str(cwd)


# 测试 处理 解包 tar 时的路径问题
# def test4(archive, path, safe_extract=False):
    # with tarfile.open(archive, mode="r:*") as tar:
def test4(path, safe_extract=False):
    with tarfile.open(mode="r|*", fileobj=sys.stdin.buffer) as tar:
        while (tarinfo := tar.next()) is not None:
            if ".." in tarinfo.name:
                if safe_extract:
                    print("成员路径包含 `..' 不提取:", tarinfo.name, file=sys.stderr)
                else:
                    print("成员路径包含 `..' 提取为:", tarinfo.name)
                    order_bad_path(pathlib.Path(tarinfo.name))

            # 安全的直接提取
            tar.extract(tarinfo, path)


if __name__ == "__main__":
    # test3(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    # test4(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    # test4(pathlib.Path(sys.argv[1]))
    # maketar(sys.argv[1], sys.argv[2], sys.argv[3:])
    maketar(sys.argv[1], sys.argv[2], True)