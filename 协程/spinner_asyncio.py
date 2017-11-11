#!/usr/bin/env python3
#coding=utf-8

import asyncio
import itertools
import sys

@asyncio.coroutine #➊
def spin(msg): #➋
    write, flush = sys.stdout.write, sys.stdout.flush
    for char in itertools.cycle('|/-\\'):
        status = char + ' ' + msg
        write(status)
        flush()
        write('\x08' * len(status))
        try:
            yield from asyncio.sleep(.1) #➌
        except asyncio.CancelledError: #➍
            break
    write(' ' * len(status) + '\x08' * len(status))

@asyncio.coroutine
def slow_function(): #➎
    # 假装等待I/O一段时间
    yield from asyncio.sleep(9)
    return 42
#➏

@asyncio.coroutine
def supervisor(): #➐
    spinner = asyncio.async(spin('thinking!'))
    print('spinner object:', spinner) #➒
    result = yield from slow_function() #➓
    spinner.cancel() #⓫
    return result
#➑
def main():
    loop = asyncio.get_event_loop() #⓬
    result = loop.run_until_complete(supervisor())
    loop.close()
    print('Answer:', result)
#⓭
if __name__ == '__main__':
    main()
