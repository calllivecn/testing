#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-21 20:39:09
# author calllivecn <c-all@qq.com>


import io
import os
import sys
import time
import enum
import shlex
import pickle
import signal
import socket
import argparse
import subprocess
from datetime import datetime

from threading import (
    Thread,
    Lock,
)
import traceback

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

BIG_SPLIT = "="*10
SMALL_SPLIT = "-"*10
BIG2_SPLIT = BIG_SPLIT*2

class Task:

    def __init__(self, cmd: Union[str, List[str]], cwd=None, env=None):
        self.cwd = cwd
        self.env = env

        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)

        elif isinstance(cmd, list):
            self.cmd = cmd
        else:
            raise ValueError(f"给出的命令格式不对")

    def run(self):
        self.start = timestamp()
        p = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env)
        self.pid = p.pid
        while (recode := p.poll()) is None:
            time.sleep(1)
        self.end = timestamp()
        self.recode = recode
        return self.recode


    def __str__(self):
        s=[]
        if self.env is not None:
            s.append(f"env: {self.env}")

        s.append(f"CWD: {self.cwd}")

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
        self.done_exit = False

        self.running = False
        self.pause_flag = False

        self.add()

    def add(self):
        """
        同队列下，添加一个执行器(并行跑一个任务队列)。
        """
        th = Thread(target=self.__exec, daemon=True)
        th.start()
        self.name = th.name

    def done(self):
        """
        当前执行，执行完后退出。
        """
        self.done_exit = True
    
    def kill(self, sig: signal.signal):
        self.done_exit = True
        os.kill(self.task.pid, sig)

    def pause(self):
        self.pause_flag = True
        os.kill(self.task.pid, signal.SIGSTOP)

    def recover(self):
        os.kill(self.task.pid, signal.SIGCONT)

    def __exec(self):
        while True:
            if self.done_exit:
                print(f"{self.name} 执行完退出")
                return

            # 当前执行器 正在执行的任务
            self.task = self.q.get()

            print(BIG2_SPLIT)
            print(f"开始时间: {timestamp()}")
            print(self.task)
            print(BIG2_SPLIT)

            self.running = True
            self.task.run()
            self.running = False

            print(BIG2_SPLIT)
            print(f"开始时间: {self.task.start}, 结束时间: {self.task.end}")
            print(self.task)
            print(BIG2_SPLIT)


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
    
    def kill(self, seq: int, sig: signal.signal = signal.SIGTERM):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths.pop(seq)
            th.kill(sig)

    def pause(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths[seq]
            th.pause()

    def recover(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths.pop(seq)
            th.recover()

    def status(self):
        buf = []
        buf.append(f"{BIG_SPLIT} 执行器(总数: {len(self.ths)}) {BIG_SPLIT}")
        for i, th in enumerate(self.ths):
            buf.append(f"{SMALL_SPLIT} 执行器编号:{i} {SMALL_SPLIT}")
            if th.running:

                if th.task.env is not None:
                    buf.append(f"ENV: {th.task.env}")

                run = f"pid: {th.task.pid} -- 执行中"
                if th.done_exit:
                    t = self.ths.pop(i)
                    run += f" -- 标记: 执行完后退出"

                if th.pause_flag:
                    run += f" -- 暂停状态(--recover恢复)"

                buf.append(run)

                buf.append(f"CMD: {th.task.cmd}")
            else:
                buf.append("等待中")

        return "\n".join(buf)
        
    def list(self):
        buf = []
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
    List = enum.auto()
    Insert = enum.auto()
    Remove = enum.auto()
    Move = enum.auto()
    Done = enum.auto()

    ADD = enum.auto()
    Kill = enum.auto()
    Pause = enum.auto()
    Recover = enum.auto()

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
        data =  client.recv(8192)
        if not data:
            print("peer close()")
            client.close()
            continue

        proto = pickle.loads(data)
        # print("type:", proto[0])

        if proto[0] == CmdType.Status:
            data = m.status()
            data = f"{'+'*10} 服务port: {port} {'+'*10}\n" + data
            reply = pickle.dumps((CmdType.Result, data))
        
        elif proto[0] == CmdType.List:
            data = m.list()
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
            try:
                m.move(i, n)
            except IndexError as e:
                reply = pickle.dumps((CmdType.ReERR,))
                traceback.print_exc()
            else: 
                reply = pickle.dumps((CmdType.ReOK,))
        
        elif proto[0] == CmdType.Done:
            i = proto[1]
            m.done_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Kill:
            i = proto[1]
            m.kill(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Pause:
            i = proto[1]
            m.pause(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Recover:
            i = proto[1]
            m.recover(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.ADD:
            i = proto[1]
            m.add_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        # client.send(reply)
        client.sendall(reply)
        client.close()
    
    sock.close()




def client(args):

    host = args.host
    port = args.port

    cwd = os.getcwd()

    if args.status:
        cmd = pickle.dumps((CmdType.Status,))
    
    elif args.list:
        cmd = pickle.dumps((CmdType.List,))
    
    elif args.task:
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))

    elif args.insert is not None:
        cmd = pickle.dumps((CmdType.Insert, args.insert, Task(args.taskcmd, cwd)))

    elif args.remove is not None:
        cmd = pickle.dumps((CmdType.Remove, args.remove))

    elif args.move:
        cmd = pickle.dumps((CmdType.Move, int(args.taskcmd[0]), int(args.taskcmd[1])))
    
    elif args.done is not None:
        cmd = pickle.dumps((CmdType.Done, args.done))

    elif args.add:
        cmd = pickle.dumps((CmdType.ADD, args.add))
    
    elif args.kill:
        cmd = pickle.dumps((CmdType.Kill, args.kill))
    
    elif args.pause:
        cmd = pickle.dumps((CmdType.Pause, args.pause))
    
    elif args.recover:
        cmd = pickle.dumps((CmdType.Recover, args.recover))
    
    else:
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))


    sock = socket.create_connection((host, port))

    sock.send(cmd)

    buf = io.BytesIO()
    while (data := sock.recv(8192)) != b"":
        buf.write(data)

    reply = pickle.loads(buf.getvalue())
    # print("reply:", reply)

    if reply[0] == CmdType.ReOK:
        recode = 0

    elif reply[0] == CmdType.ReERR:
        print("有什么出错了, 查看服务端日志。")
        recode = 1

    elif reply[0] == CmdType.Result:
        # print(reply[1])
        try:
            print(reply[1], flush=True)
        except BrokenPipeError:
            pass

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
    option.add_argument("--host", default="::1", help="默认地址(server: '::', or client: '::1'， 如果有BATCH_TASK_HOST环境变量优先使用)")
    option.add_argument("--port", type=int, default=1122, help="server 地址(default: 1122，如果有BATCH_TASK_PORT环境变量优先使用)")

    c = parse.add_argument_group(title="client 参数")
    group = c.add_mutually_exclusive_group()
    group.add_argument("--add-executer", dest="add", type=int, help="添加一个并行执行器")
    group.add_argument("--done-executer", dest="done", type=int, help="指定一个执行器，本次执行完后退出。(减少一个并行执行)")
    group.add_argument("--kill", type=int, help="kill一个执行器(减少一个并行执行)")
    group.add_argument("--pause", type=int, help="暂停一个正在的执行器")
    group.add_argument("--recover", type=int, help="恢复一个正在的执行器")

    c.add_argument("--task", action="store_true", help="任务(默认选项)")

    group.add_argument("--status", action="store_true", help="查看状态")
    group.add_argument("--list", action="store_true", help="查看队列")
    group.add_argument("--insert", type=int, help="在队列指定位置插入新任务")
    group.add_argument("--remove", type=int, help="删除队列指定位置任务")
    group.add_argument("--move", action="store_true", help="删除队列指定位置任务")

    parse.add_argument("taskcmd", nargs="*", help="需要执行的命令行")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        # parse.print_help()
        sys.exit(0)

    ENV_HOST = os.environ.get("BATCH_TASK_HOST")
    ENV_PORT = os.environ.get("BATCH_TASK_PORT")

    if args.server:
        args.host = ENV_HOST if ENV_HOST else "::1"
        args.port = int(ENV_PORT) if ENV_PORT else args.port

        try:
            server(args)
        except KeyboardInterrupt:
            pass

        sys.exit(0)
    
    if ENV_PORT:
        args.port = int(ENV_PORT)

    client(args)


if __name__ == "__main__":
    main()
