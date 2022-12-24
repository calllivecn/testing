#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-19 01:57:55
# author calllivecn <c-all@qq.com>


import os
import sys
import stat
import errno
import logging
import asyncio
from argparse import ArgumentParser
from functools import  lru_cache
from collections import defaultdict

try:
    import faulthandler
except ImportError:
    pass
else:
    faulthandler.enable()


import pyfuse3
import pyfuse3_asyncio
pyfuse3_asyncio.enable()
from pyfuse3 import FUSEError

"""
from .crypto import (
    FileFormat,
    fileinfo,
    encrypt,
    decrypt,
    key_deriverd,
)
"""
def func_name(func):
    def wrap(*args, **kwargs):
        log.debug(f"func name: {func.__name__=}, {args=} {kwargs=}")
        return func(*args, **kwargs)

    return wrap

log = logging.getLogger("AesFS")

class AesFS(pyfuse3.Operations):

    enable_writeback_cache = True

    def __init__(self, source):
        super().__init__()
        self.root_inode = pyfuse3.ROOT_INODE
 
        self._inode_path_map = { pyfuse3.ROOT_INODE: source }

        # 看着像引用计数
        self._lookup_cnt = defaultdict(lambda : 0)
        self._fd_inode_map = {}
        self._inode_fd_map = {}
        self._fd_open_count = {}

    def _inode_to_path(self, inode):
        try:
            val = self._inode_path_map[inode]
        except KeyError:
            raise FUSEError(errno.ENOENT)

        if isinstance(val, set):
            #如果要进行硬链接，请选择任何路径
            val = next(iter(val))
        return val


    def _add_path(self, inode, path):
        log.debug(f"_add_path(): {inode=}, {path=}")
        self._lookup_cnt[inode] += 1

        #使用硬链接，一个Inode可能会映射到多个路径。
        if inode not in self._inode_path_map:
            self._inode_path_map[inode] = path
            return

        val = self._inode_path_map[inode]
        if isinstance(val, set):
            val.add(path)
        elif val != path:
            self._inode_path_map[inode] = { path, val }

    # @lru_cache
    async def getattr(self, inode, ctx=None):
        entry = pyfuse3.EntryAttributes()

            # raise pyfuse3.FUSEError(errno.ENOENT)
        # os.stat()

        stamp = int(1438467123.985654 * 1e9)
        entry.st_atime_ns = stamp
        entry.st_ctime_ns = stamp
        entry.st_mtime_ns = stamp
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode

        return entry

    async def lookup(self, parent_inode, name, ctx=None):
        if parent_inode != pyfuse3.ROOT_INODE or name != self.hello_name:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return await self.getattr(self.hello_inode)
    
    async def rename(self, parent_inode_old, name_old, parent_inode_new, name_new, flags, ctx):
        log.debug(f"{self.rename.__func__=}, {parent_inode_old=}, {name_old=}, {parent_inode_new=}, {name_new=}, {flags=}, {ctx=}")
        
        # raise pyfuse3.FUSEError(errno.ENOENT)


    async def opendir(self, inode, ctx):
        if inode != pyfuse3.ROOT_INODE:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return inode

    async def readdir(self, fh, start_id, token):
        # assert fh == pyfuse3.ROOT_INODE

        # only one entry
        if start_id == 0:
            pyfuse3.readdir_reply(token, self.hello_name, await self.getattr(self.hello_inode), 1)
        return

    async def setxattr(self, inode, name, value, ctx):
        if inode != pyfuse3.ROOT_INODE or name != b'command':
            raise pyfuse3.FUSEError(errno.ENOTSUP)

        if value == b'terminate':
            pyfuse3.terminate()
        else:
            raise pyfuse3.FUSEError(errno.EINVAL)

    async def open(self, inode, flags, ctx):
        if inode != self.hello_inode:
            raise pyfuse3.FUSEError(errno.ENOENT)
        if flags & os.O_RDWR or flags & os.O_WRONLY:
            raise pyfuse3.FUSEError(errno.EACCES)
        return pyfuse3.FileInfo(fh=inode)

    async def read(self, fh, off, size):
        assert fh == self.hello_inode
        return self.hello_data[off:off+size]


def init_logging(debug=False):
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(threadName)s: [%(name)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)



def parse_args():
    '''Parse command line'''

    parser = ArgumentParser()

    parser.add_argument('source', type=str, help='AesFS 目录')
    parser.add_argument('mountpoint', type=str, help='挂载点')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False, help='Enable FUSE debugging output')
    return parser.parse_args()


def main():
    args = parse_args()
    init_logging(args.debug)

    aesfs = AesFS(args.source)
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=aesfs')

    if args.debug_fuse:
        fuse_options.add('debug')

    pyfuse3.init(aesfs, args.mountpoint, fuse_options)
    try:
        asyncio.run(pyfuse3.main())
    except BaseException:
        pyfuse3.close(unmount=False)
        raise

    pyfuse3.close()


if __name__ == '__main__':
    main()
