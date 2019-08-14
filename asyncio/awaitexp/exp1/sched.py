"""A very simple co-routine scheduler.

Note: this is written to favour simple code over performance.
"""
from types import coroutine


#@coroutine
async def switch():
    yield

import time,asyncio

#@asyncio.coroutine
async def S():
    print('switch end')
    #yield asyncio.sleep(1)
    await asyncio.sleep(1)


def run(coros):
    """Execute a list of co-routines until all have completed."""
    # Copy argument list to avoid modification of arguments.
    coros = list(coros)

    while len(coros):
        # Copy the list for iteration, to enable removal from original
        # list.
        for coro in list(coros):
            try:
                coro.send(None)
            except StopIteration:
                coros.remove(coro)
