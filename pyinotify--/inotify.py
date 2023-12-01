#!/usr/bin/env python3
# coding=utf-8
# date 2023-11-30 19:33:11
# author calllivecn <c-all@qq.com>


import os
import sys
import enum
import errno
import ctypes
import selectors

from ctypes import util
from pathlib import Path

from typing import (
    List,
    Tuple,
    Union,
)

__all__ = (
    "IN_ALL_EVENTS",
    "E",
    "Notify",
)

class E(enum.IntEnum):

    # Supported events suitable for MASK parameter of INOTIFY_ADD_WATCH.
    IN_ACCESS = 0x00000001
    IN_MODIFY = 0x00000002
    IN_ATTRIB = 0x00000004
    IN_CLOSE_WRITE = 0x00000008
    IN_CLOSE_NOWRITE = 0x00000010
    IN_CLOSE = IN_CLOSE_WRITE | IN_CLOSE_NOWRITE
    IN_OPEN = 0x00000020
    IN_MOVED_FROM = 0x00000040
    IN_MOVED_TO = 0x00000080
    IN_MOVE = IN_MOVED_FROM | IN_MOVED_TO
    IN_CREATE = 0x00000100
    IN_DELETE = 0x00000200
    IN_DELETE_SELF = 0x00000400
    IN_MOVE_SELF = 0x00000800

    # Events sent by the kernel.
    IN_UNMOUNT = 0x00002000
    IN_Q_OVERFLOW = 0x00004000 # Event queued overflowed.
    IN_IGNORED = 0x00008000 # File was ignored.

    # /* Special flags.  */
    IN_ONLYDIR = 0x01000000 # Only watch the path if it is a directory.  */
    IN_DONT_FOLLOW = 0x02000000 # /* Do not follow a sym link.  */
    IN_EXCL_UNLINK = 0x04000000 # /* Exclude events on unlinked objects.  */
    IN_MASK_CREATE = 0x10000000 # /* Only create watches.  */
    IN_MASK_ADD = 0x20000000 # /* Add to the mask of an already existing watch.  */
    IN_ISDIR = 0x40000000 # /* Event occurred against dir.  */
    IN_ONESHOT = 0x80000000 # /* Only send event once.  */

    """
    IN_ALL_EVENTS = (
        IN_ACCESS|IN_MODIFY|IN_ATTRIB|IN_CLOSE_WRITE|IN_CLOSE_NOWRITE|IN_CLOSE|IN_OPEN|IN_MOVED_FROM|IN_MOVED_TO|IN_MOVE|IN_CREATE|IN_DELETE|IN_DELETE_SELF|IN_MOVE_SELF
    )
    """


IN_ALL_EVENTS = 0x0
for e in E:
    if e <= E.IN_MOVE_SELF:
        IN_ALL_EVENTS |= e.value


class Event(ctypes.Structure):

    _fields_ = [
        ("wd", ctypes.c_int), # 指向发生事件的监控项的文件描述符，该字段值由之前对 inotify_add_watch() 的调用返回。用于区分是哪个监控项触发了该事件
        ("mask", ctypes.c_uint32), # inotify 事件的一位掩码
        ("cookies", ctypes.c_uint32), # 唯一的关联 inotify 事件的值
        ("len", ctypes.c_uint32), # 分配给 name 的字节数
        # ("name", ctypes.c_char), # 标识触发该事件的文件名
    ]


class Notify:

    def __init__(self):
        self._libc = ctypes.CDLL(util.find_library("c"), use_errno=True)

        if not hasattr(self._libc, "inotify_init"):
            raise OSError("inotify_init() not found.")

        self._init = self._libc.inotify_init
        self._init.restype = ctypes.c_int

        self._add_watch = self._libc.inotify_add_watch
        self._add_watch.restype = ctypes.c_int
        self._add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]

        self._rm_watch = self._libc.inotify_rm_watch
        self._rm_watch.restype = ctypes.c_int
        self._rm_watch.argtypes = [ctypes.c_int, ctypes.c_uint32]

        self._read = self._libc.read
        self._read.restype = ctypes.c_ssize_t
        # self._read.restype = ctypes.POINTER(Event)
        self._read.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]

        self.fd = self._init()

        if self.fd == -1:
            raise OSError(f"inotify_init() errno: {errno.errno}")
        
        # 已经 watch 的路径
        self.wd = {}

        # 如果是递归模式
        self._recursive = False
        self.mask = None

    
    def inotify_add_watch(self, path: Union[Path, str], mask: int):

        if isinstance(path, str):
            path_ptr = ctypes.create_string_buffer(path.encode("utf-8"))
            path = Path(path)
        elif isinstance(path, Path):
            path_ptr = ctypes.create_string_buffer(str(path).encode("utf-8"))
        else:
            raise TypeError("argument path: Union[Path, str]")

        wd = self._add_watch(self.fd, path_ptr, mask)

        if self.wd.get(path):
            return

        self.wd[wd] = path
    

    def inotify_rm_watch(self, fd_watch: int) -> int:
        if self.wd.get(fd_watch):
            return self._rm_watch(self.fd, fd_watch)
        else:
            return -1
    

    def read(self) -> List[Tuple[Event, str]]:

        buf = ctypes.create_string_buffer(4096)
        buf_len = 4096
        nbytes = self._read(self.fd, buf, buf_len)
        if nbytes == -1:
            raise OSError(f"inotify read() errno: {errno.errno}")

        e_size = ctypes.sizeof(Event) # 16byte
        es = []
        i = 0
        # print(f"{buf_len=} {nbytes=}")
        while i < nbytes:
            i_e_size = i + e_size
            e = Event.from_buffer_copy(buf[i:i_e_size])

            name = self.__name_parse(buf[i_e_size:i_e_size+e.len])

            # 把mask转换为一个个Event
            e_ones = self.__event_merge(e.mask)
            # print(f"{e.wd=}, {hex(e.mask)=}, {e.cookies=}, {e.len=}, {name=}")

            pathname = self.__path_merge(e, name)
            es.append((e_ones, pathname))

            # 如果是递归模式？
            if self._recursive:
                if e.mask & E.IN_ISDIR and e.mask & E.IN_CREATE:
                    if not e.wd in self.wd:
                        self.inotify_add_watch(pathname, self.mask)

                elif e.mask & E.IN_ISDIR and e.mask & E.IN_DELETE:
                    pass

            i = i_e_size + e.len

        return es
    

    def inotify_add_watch_recursive(self, path: Union[Path, str], mask: int):

        self._recursive = True

        for dirpath, dirnames, filenames in os.walk(path):
            # self.
            pass


    def __event_merge(self, mask) -> Tuple[Event]:
        events = []
        for e in E:
            if mask & e:
                events.append(e)

        return tuple(events)


    def __name_parse(self, name: bytes) -> str:
            name = name[:name.find(b"\0")]
            return name.decode("utf-8")
    

    def __path_merge(self, e: Event, name: Union[Path, str]) -> Path:

        try:
            dirname = self.wd[e.wd]
        except ValueError:
            return Path("")
        
        return dirname / name




def test():

    path = Path(sys.argv[1])

    ni = Notify()

    ni.inotify_add_watch(path, IN_ALL_EVENTS)

    while True:
        es = ni.read()
        # print(f"这次: {len(es)=}")
        for e, name in es:
            print(f"{e}, {name=}")


if __name__ == "__main__":
    test()