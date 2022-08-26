#!/usr/bin/env python3
# coding=utf-8
# date 2022-08-18 07:59:52
# author calllivecn <c-all@qq.com>

import os
import threading


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
        os.close(self.w)
    
    def close2(self):
        os.close(self.r)


def output(pipe, threadname=None):
    while (data := pipe.read(32)) != b"":
        print(threadname, "pipe.read():", data)

    print("output 执行完成")


def test1():
    pipe = Pipe()
    th1 = threading.Thread(target=output, args=(pipe,), daemon=True)
    th1.start()

    for i in range(50):
        pipe.write(i.to_bytes(4, "big"))
    pipe.close()
    th1.join()
    pipe.close2()


class Pipefork:
    """
                 / --> read(stream1, size)
    write() --> |
                 \ --> read(stream2, size)
                  \ --> read(stram3, size)
                   \ --> ...
                    \ --> ...
    """
    def __init__(self):
        """
        fork >=2, 看着可以和pipe 功能合并。
        """
        self.pipes = []
    
    def fork(self):
        pipe = Pipe()
        self.pipes.append(pipe)
        return pipe
    
    def write(self, data):
        for pipe in self.pipes:
            n = pipe.write(data)
        return n

    def close(self):
        for pipe in self.pipes:
            pipe.close()

    def close2(self):
        for pipe in self.pipes:
            pipe.close2()

def input(pipe):
    for i in range(1<<20):
        pipe.write(i.to_bytes(4, "big"))
    pipe.close()

def test2():
    pipe = Pipefork()
    split = pipe.fork()
    sha = pipe.fork()

    n = "input"
    th0 = threading.Thread(target=input, args=(pipe,), name=n, daemon=True)
    th0.start()

    n = "split--"
    th1 = threading.Thread(target=output, args=(split, n), name=n, daemon=True)
    th1.start()

    n = "sha--"
    th2 = threading.Thread(target=output, args=(sha, n), name=n, daemon=True)
    th2.start()

    th1.join()
    th2.join()
    pipe.close2()

if __name__ == "__main__":
    # test1()
    test2()