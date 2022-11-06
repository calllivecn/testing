
import sys
import time
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
        self.start = timestamp()
        p = subprocess.Popen(self.cmd, self.cwd, self.env)
        self.pid = p.pid
        while (recode := p.poll()) is not None:

            if self._exit:
                p.terminate()
                print(f"中止执行:\n{self}")
                break

            time.sleep(1)

        self.end = timestamp()
        self.recode = recode
        return self.recode



HOST = ""
PORT = 1122
ADDR=(HOST, PORT)

def server():
    sock = socket.create_server(ADDR, family=socket.AF_INET6, dualstack_ipv6=True)

    while True:
        client, addr = sock.accept()
        print(addr)
        data =  client.recv(8192)
        task = pickle.loads(data)
        print("task:", task)

        print("cmd: ", task.cmd)

        client.close()
        


def client():

    task = Task("hostname listlkjife")

    sock = socket.create_connection(("localhost", PORT))

    data = pickle.dumps(task)
    print("unpickle(task):", data)
    sock.send(data)

    sock.close()


if __name__ == "__main__":

    if sys.argv[1] == "server":
        server()
    else:
        client()