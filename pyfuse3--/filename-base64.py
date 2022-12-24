#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-19 01:57:55
# author calllivecn <c-all@qq.com>

"""
先写个，把文件名都变成base64编码的试试水
"""


import os
import sys
import stat
import errno
import base64
import logging
import asyncio
import argparse
from pathlib import Path
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


log = logging.getLogger(__name__)


def func_name(func):
    def wrap(*args, **kwargs):
        log.debug(f"{func.__name__=}: {args=} {kwargs=}")
        return func(*args, **kwargs)

    return wrap


class Base64FS(pyfuse3.Operations):

    # supports_dot_lookup = True
    enable_writeback_cache = True

    def __init__(self, source: Path):
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


    @func_name
    async def readdir(self, fh, start_id, token):
        path = self._inode_to_path(fh)
        log.debug(f"readdir(): {fh=}, {path=}, {start_id=}")

        entries = []
        # for name in os.listdir(path):
        for name in pyfuse3.listdir(str(path)):
            if name == '.' or name == '..':
                continue
            dir_p = path / name
            attr = self._getattr_path(dir_p)
            entries.append((attr.st_ino, dir_p, attr))
        
        log.debug(f"read {len(entries)=} entries, starting at {start_id=}")

        for (ino, p_name, attr) in sorted(entries):
            log.debug(f"entries: {(ino, p_name, attr)=}")
            if ino <= start_id:
                continue
            r = pyfuse3.readdir_reply(token, os.fsencode(p_name), attr, ino+1)
            if r:
                log.debug(f"readdir_reply() --> {r}")
            else:
                break

            self._add_path(ino, p_name)
        
        return False


    # @lru_cache
    @func_name
    async def getattr(self, inode, ctx=None):
        if inode in self._inode_fd_map:
            return self._getattr_fd(inode)
        else:
            path = self._inode_to_path(inode)
            return self._getattr_path(path)


    @func_name
    def _getattr_path(self, path: Path):
        entry = pyfuse3.EntryAttributes()
        try:
            st = os.stat(path)
        except OSError as exc:
            raise FUSEError(exc.errno)

        for attr in ('st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                     'st_rdev', 'st_size', 'st_atime_ns', 'st_mtime_ns',
                     'st_ctime_ns'):
            setattr(entry, attr, getattr(st, attr))

        entry.generation = 0
        entry.entry_timeout = 0
        entry.attr_timeout = 0
        entry.st_blksize = 512
        entry.st_blocks = ((entry.st_size+entry.st_blksize-1) // entry.st_blksize)

        return entry


    def _getattr_fd(self, fd):
        try:
            fstat = os.fstat(fd)
        except OSError as e:
            raise FUSEError(e.errno)

        entry = pyfuse3.EntryAttributes()

        for attr in ('st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                     'st_rdev', 'st_size', 'st_atime_ns', 'st_mtime_ns',
                     'st_ctime_ns'):
            setattr(entry, attr, getattr(fstat, attr))
        entry.generation = 0
        entry.entry_timeout = 0
        entry.attr_timeout = 0
        entry.st_blksize = 512
        entry.st_blocks = ((entry.st_size+entry.st_blksize-1) // entry.st_blksize)

        return entry


    @func_name
    async def lookup(self, parent_inode, name, ctx=None):

        if name in (".", ".."):
            log.debug("lookup() --> . & .. : {name}")

        parent = self._inode_to_path(parent_inode)

        p = parent / os.fsdecode(name)
        log.debug(f"lookup() --> path: {p} in node:{parent_inode}")

        b64 = base64.b64encode(str(p).encode())
            # raise pyfuse3.FUSEError(errno.ENOENT)
        entry = self._getattr_path(p)

        if name != '.' and name != '..':
            self._add_path(entry.st_ino, p)
        else:
            log.debug(f"lookup() --> . or ..: {entry}")
        return entry


    # async def rename(self, parent_inode_old, name_old, parent_inode_new, name_new, flags, ctx):
        # log.debug(f"{self.rename.__func__=}, {parent_inode_old=}, {name_old=}, {parent_inode_new=}, {name_new=}, {flags=}, {ctx=}")
        # raise pyfuse3.FUSEError(errno.ENOENT)


    @func_name
    async def opendir(self, inode, ctx):
        return inode


    """
    async def setxattr(self, inode, name, value, ctx):
        if inode != pyfuse3.ROOT_INODE or name != b'command':
            raise pyfuse3.FUSEError(errno.ENOTSUP)

        if value == b'terminate':
            pyfuse3.terminate()
        else:
            raise pyfuse3.FUSEError(errno.EINVAL)
    """

    @func_name
    async def statfs(self, ctx):
        root = self._inode_path_map[pyfuse3.ROOT_INODE]
        stat_ = pyfuse3.StatvfsData()
        try:
            statfs = os.statvfs(root)
        except OSError as exc:
            raise FUSEError(exc.errno)
        for attr in ('f_bsize', 'f_frsize', 'f_blocks', 'f_bfree', 'f_bavail',
                     'f_files', 'f_ffree', 'f_favail'):
            setattr(stat_, attr, getattr(statfs, attr))
        stat_.f_namemax = statfs.f_namemax - (len(os.fsencode(root))+1)
        return stat_


    @func_name
    async def open(self, inode, flags, ctx):
        if inode in self._inode_fd_map:
            fd = self._inode_fd_map[inode]
            self._fd_open_count[fd] += 1
            return pyfuse3.FileInfo(fh=fd)

        assert flags & os.O_CREAT == 0

        try:
            fd = os.open(self._inode_to_path(inode), flags)
        except OSError as exc:
            raise FUSEError(exc.errno)

        self._inode_fd_map[inode] = fd
        self._fd_inode_map[fd] = inode
        self._fd_open_count[fd] = 1
        return pyfuse3.FileInfo(fh=fd)


    @func_name
    async def create(self, inode_p, name, mode, flags, ctx):
        path = self._inode_to_path(inode_p) / name

        try:
            fd = os.open(path, flags | os.O_CREAT | os.O_TRUNC)
        except OSError as exc:
            raise FUSEError(exc.errno)

        attr = await self.getattr(inode_p)
        self._add_path(attr.st_ino, path)
        self._inode_fd_map[attr.st_ino] = fd
        self._fd_inode_map[fd] = attr.st_ino
        self._fd_open_count[fd] = 1

        return (pyfuse3.FileInfo(fh=fd), attr)


    @func_name
    async def read(self, fd, offset, length):
        os.lseek(fd, offset, os.SEEK_SET)
        return os.read(fd, length)


    @func_name
    async def write(self, fd, offset, buf):
        os.lseek(fd, offset, os.SEEK_SET)
        return os.write(fd, buf)


    async def release(self, fd):
        if self._fd_open_count[fd] > 1:
            self._fd_open_count[fd] -= 1
            return

        del self._fd_open_count[fd]
        inode = self._fd_inode_map[fd]
        del self._inode_fd_map[inode]
        del self._fd_inode_map[fd]
        try:
            os.close(fd)
        except OSError as exc:
            raise FUSEError(exc.errno)


def init_logging(debug=False):
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d [%(name)s]: %(filename)s:%(lineno)s %(message)s',
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

    parser = argparse.ArgumentParser()

    parser.add_argument('source', type=Path, help='Base64FS 目录')
    parser.add_argument('mountpoint', type=str, help='挂载点')

    parser.add_argument('--parse', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False, help='Enable FUSE debugging output')

    args = parser.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)
    
    return args


def main():
    args = parse_args()
    init_logging(args.debug)

    base64fs = Base64FS(args.source)
    log.debug(f"f{base64fs.supports_dot_lookup=}")
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=base64fs')

    if args.debug_fuse:
        fuse_options.add('debug')

    pyfuse3.init(base64fs, args.mountpoint, fuse_options)
    try:
        asyncio.run(pyfuse3.main())
    except BaseException:
        # pyfuse3.close(unmount=False)
        pyfuse3.close()
        raise


if __name__ == '__main__':
    main()
