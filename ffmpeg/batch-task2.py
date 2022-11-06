#!/usr/bin/env python3


import os
import sys
import time
import enum
import glob
import shlex
import pickle
import socket
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

from threading import (
    Thread,
    Lock,
)

from typing import (
    Union,
    List,
)

def timestamp():
    t = datetime.now()
    return t.strftime("%Y-%m-%d %H:%M:%S")


def infile(f):
    with open(f) as f:
        tmp = f.readlines()

    return [ l.rstrip("\n") for l in tmp ]


class Task:

    def __init__(self, cmd: Union[str, list[str]], cwd=None, env=None):
        self.cwd = cwd
        self.env = env

        self._exit = False

        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)

        elif isinstance(cmd, list):
            self.cmd = cmd
        else:
            raise ValueError(f"给出的命令格式不对")

    def run(self):
        print("start: task.run():")
        self.start = timestamp()
        p = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env)
        self.pid = p.pid
        while (recode := p.poll()) is None:

            if self._exit:
                p.terminate()
                print(f"中止执行:\n{self}")
                break
            time.sleep(1)

        self.end = timestamp()
        self.recode = recode
        return self.recode

    def kill(self):
        self._exit = True

    def __str__(self):
        s=[]
        s.append(f"env: {self.env}")
        s.append(f"cwd: {self.cwd}")
        if hasattr(self, "pid"):
            s.append(f"PID: {self.pid}")
        s.append(f"CMD: {self.cmd}")
        if hasattr(self, "recode"):
            s.append(f"recode: {self.recode}")
        
        return "\n".join(s)


class Q(List):
    """
    可以调整顺序 任务队列
    """

    def __init__(self, maxlen=1000):
        self.maxlen = maxlen
        self._lock = Lock()
        self._empty_full_lock = Lock().acquire()

    def put(self, item):
        # print("Q put():", item)
        with self._lock:
            self.append(item)
    
    def get(self):
        while len(self) <= 0:
            # print("q.get() wait...")
            time.sleep(1)

        with self._lock:
            return self.pop(0)

    def insert(self, i, item):
        with self._lock:
            super().insert(i, item)
    
    def move(self, i, n):
        with self._lock:
            self[i], self[n] = self[n], self[i]
    
    def remove(self, i):
        with self._lock:
            self.pop(i)


class Executer:
    """
    先只支持一个 执行器吧
    """
    def __init__(self, queue: Q):
        self.q = queue
        self._done = False

        self.running = False
        self.add()

    def add(self):
        """
        同队列下，添加一个执行器(并行跑一个任务队列)。
        """
        th = Thread(target=self.__exec)
        th.start()

    def done(self):
        """
        当前执行，执行完后退出。
        """
        self._done = True

    def __exec(self):
        while True:
            if self._done:
                return

            # 当前执行器 正在执行的任务
            self.task = self.q.get()

            print("="*40)
            print(f"开始时间: {timestamp()}")
            print(self.task)
            print("="*40)

            self.running = True
            self.task.run()
            self.running = False

            print("="*40)
            print(f"开始时间: {self.task.start}, 结束时间: {self.task.end}")
            print(self.task)
            print("="*40)


class Manager:
    """
    执行器之间是并行关系，每个执行器属于一个执行队列。
    """

    def __init__(self):
        self.q = Q()
        # {queue-name: TaskQeueu}

        # 执行器s
        self.ths = []
        self.ths.append(Executer(self.q))

    def add_task(self, task: Task):
        self.q.put(task)

    def add_executer(self, i: int):
        for _ in range(i):
            self.ths.append(Executer(self.q))

    def done_executer(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            t = self.ths[seq]
            t.done()

    def status(self):
        buf = []
        buf.append(f"执行器(总数: {len(self.ths)}):")
        for i, th in enumerate(self.ths):
            s = f"执行中(pid: {th.task.pid}) -- CMD: {th.task.cmd}" if th.running else "等待中"
            buf.append(f"编号:{i}: {s}")
        
        buf.append(f"任务队列(总数: {len(self.q)}):")
        for i, task in enumerate(self.q):
            s = "="*10
            buf.append(f"{s} 任务号:{i} {s}\n{str(task)}")

        return "\n".join(buf)

    def insert(self, i: int, task: Task):
        self.q.insert(i, task)

    def remove(self, i: int):
        self.q.remove(i)

    def move(self, i: int, n: int):
        self.q.move(i, n)

# 两边传输
class CmdType(enum.IntEnum):
    
    Status = 0x01
    Task = enum.auto()
    Insert = enum.auto()
    Remove = enum.auto()
    Move = enum.auto()
    Done = enum.auto()
    ADD = enum.auto()

    # 回复client的type
    ReOK = enum.auto()
    ReERR = enum.auto()
    Result = enum.auto()


def server(args):
    host = args.host
    port = args.port

    print(f"启动执行管理器: {host}:{port}")

    m = Manager()

    sock = socket.create_server((host, port), family=socket.AF_INET6, dualstack_ipv6=True)

    while True:
        client, addr = sock.accept()
        # print(addr)
        data =  client.recv(8192)
        proto = pickle.loads(data)
        # print("type:", proto[0])

        if proto[0] == CmdType.Status:
            data = m.status()
            reply = pickle.dumps((CmdType.Result, data))
        
        elif proto[0] == CmdType.Task:
            task = proto[1]
            # print(f"添加任务：{task.cmd}")
            m.add_task(task)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Insert:
            number = proto[1]
            task = proto[2]
            m.insert(number, task)

            reply = pickle.dumps((CmdType.ReOK,))
        
        elif proto[0] == CmdType.Remove:
            number = proto[1]
            m.remove(number)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Move:
            i, n = proto[1], proto[2]
            m.move(i, n)
            
            reply = pickle.dumps((CmdType.ReOK,))
        
        elif proto[0] == CmdType.Done:
            i = proto[1]
            m.done_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.ADD:
            i = proto[1]
            m.add_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        client.send(reply)
        client.close()




def client(args):

    host = args.host
    port = args.port

    cwd = os.getcwd()

    if args.status:
        cmd = pickle.dumps((CmdType.Status,))
    
    elif args.task:
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))

    elif args.insert:
        cmd = pickle.dumps((CmdType.Insert, args.insert, Task(args.taskcmd, cwd)))

    elif args.remove:
        cmd = pickle.dumps((CmdType.Remove, args.remove))

    elif args.move:
        cmd = pickle.dumps((CmdType.Move, args.taskcmd[0], args.taskcmd[1]))
    
    elif args.done:
        cmd = pickle.dumps((CmdType.Done, args.done))

    elif args.add:
        cmd = pickle.dumps((CmdType.ADD, args.add))
    
    else:
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))


    sock = socket.create_connection((host, port))

    sock.send(cmd)
    data = sock.recv(8192)
    reply = pickle.loads(data)
    # print("reply:", reply)

    if reply[0] == CmdType.ReOK:
        recode = 0

    elif reply[0] == CmdType.ReERR:
        print("有什么出错了")
        recode = 1

    elif reply[0] == CmdType.Result:
        # from pprint import pprint
        # pprint(reply[1])
        print(reply[1])
        recode = 0

    else:
        print("未知返回")
        recode = 1

    sock.close()
    sys.exit(recode)



def main():

    parse = argparse.ArgumentParser()

    option = parse.add_argument_group(title="通用参数")
    option.add_argument("--server", action="store_true", help="启动server端")
    option.add_argument("--host", default="::1", help="默认地址(server: '::', or client: '::1')")
    option.add_argument("--port", type=int, default=1122, help="server 地址(default: 1122)")

    c = parse.add_argument_group(title="client 参数")
    group = c.add_mutually_exclusive_group()
    group.add_argument("--add-executer", dest="add", type=int, help="添加一个并行执行器")
    group.add_argument("--done-executer", dest="done", type=int, help="指定一个执行器，本次执行完后退出。(减少一个并行执行)")

    c.add_argument("--task", action="store_true", help="任务(默认选项)")

    group.add_argument("--status", action="store_true", help="查看状态")
    group.add_argument("--insert", type=int, help="在队列指定位置插入新任务")
    group.add_argument("--remove", type=int, help="删除队列指定位置任务")
    group.add_argument("--move", action="store_true", help="删除队列指定位置任务")

    parse.add_argument("taskcmd", nargs="*", help="需要执行的命令行")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    #group = parse.add_mutually_exclusive_group()
    #group.add_argument("-i", "--infile", type=Path, help="从文件读取输入，一行一个文件。")
    #group.add_argument("files", nargs="*", help="输入的 *.mp4")

    args = parse.parse_args()

    if args.parse:
        print(args)
        parse.print_help()
        sys.exit(0)


    if args.server:
        args.host = ""
        server(args)
    
    client(args)


if __name__ == "__main__":
    main()
