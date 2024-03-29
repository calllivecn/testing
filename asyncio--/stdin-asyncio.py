#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-04 12:01:43
# author calllivecn <c-all@qq.com>

import sys
import asyncio


async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    #await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)
    #w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout.buffer)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer


async def main():
    reader, writer = await connect_stdin_stdout()
    while True:
        res = await reader.read(100)
        if not res:
            break
        writer.write(res)


if __name__ == "__main__":
    asyncio.run(main())
