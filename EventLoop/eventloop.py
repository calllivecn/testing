#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-17 03:02:30
# author calllivecn <c-all@qq.com>


import os
import time
import queue
import select
import socket


class EventLoop:
    IDLE_SECONDS = 0.05

    def __init__(self):
        self.time_queue = queue.PriorityQueue()
        self.io_read_queue = {}           # fd -> callback
        self.io_write_queue = {}
        self.io_exception_queue = {}

    def run(self):
        while True:
            self.handle_time()
            self.poll_io()
            time.sleep(self.IDLE_SECONDS)        # save cpu usage

    def handle_time(self):
        now = time.time()
        while not self.time_queue.empty():
            timeout, callback = self.time_queue.get()
            if now < timeout:
                self.time_queue.put((timeout, callback))
                break
            callback()

    def poll_io(self):
        readable_fds, writable_fds, ex_fds = select.select(self.io_read_queue.keys(),
                                                           self.io_write_queue.keys(),
                                                           self.io_exception_queue.keys(),0)
        for fd in readable_fds:
            self.io_read_queue[fd](fd)      # fd as callback argument
        for fd in writable_fds:
            self.io_write_queue[fd](fd)


def set_timeout(seconds, callback):
    global_loop.time_queue.put((time.time()+seconds, callback))

def set_interval(seconds, callbacks):
    next_run = [time.time()+seconds]      # use array because python doesn't support closure..
    def run_and_reschedule():
        next_run[0] += seconds
        global_loop.time_queue.put((next_run[0], run_and_reschedule))
        callbacks()
    global_loop.time_queue.put((next_run[0], run_and_reschedule))

def getlines(callback, fd=0):                   # fd 0 == stdin
    def read(fd):
        line = os.read(fd, 10000).decode()
        callback(line)
    global_loop.io_read_queue[fd] = read

def getHttp(host, port, path, callback):
    s = socket.socket()
    s.connect((host, port))
    s.send(f"GET {path} HTTP/1.1\r\nHost:{host}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n".encode())
    buffer = []
    def read_exhaust(fd):
        part = os.read(fd, 4000).decode()   # 4k buffer
        buffer.append(part)
        if not part or part[-4:] == "\r\n\r\n":
            del global_loop.io_read_queue[s.fileno()]
            s.close()
            callback("".join(buffer))
    global_loop.io_read_queue[s.fileno()] = read_exhaust


global_loop = EventLoop()

def main_test():
    set_timeout(30, lambda : exit())
    getHttp("baidu.com", 80, "/", lambda tcpdata: print(tcpdata))
    getlines(lambda line: print(f"stdin: {line}"))
    set_timeout(5, lambda : print("====after 5 seconds"))
    set_timeout(2, lambda : print("====after 2 seconds"))
    cnt = [1]
    set_interval(1, lambda : print(f"----interval {cnt[-1]}") or cnt.append(cnt[-1]+1))

main_test()
global_loop.run()
