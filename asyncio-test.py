'''
import asyncio

@asyncio.coroutine
def hello():
    print("Hello world!")
    # 异步调用asyncio.sleep(1):
    r = yield from asyncio.sleep(5)
    print("Hello again!")

# 获取EventLoop:
loop = asyncio.get_event_loop()
# 执行coroutine
loop.run_until_complete(hello())
loop.close()
'''

from threading import currentThread
import asyncio

@asyncio.coroutine
def hello():
    print('Hello world! {}'.format(threading.currentThread()))
    yield from asyncio.sleep(1)
    print('Hello again! {}'.format(threading.currentThread()))
'''
loop = asyncio.get_event_loop()
tasks = [hello(), hello()]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
'''






# async def 

from selectors import DefaultSelector,EVENT_READ,EVENT_WRITE



'''
async def async1(s='hello'):
	print(s + ' start')
	await asyncio.sleep(3)
	print(s + ' end')


async1()
'''



async def coro1():
    print("C1: Start")
    print("C1: Stop")


async def coro2():
	print("C2: Start")
	print("C2: a")
	print("C2: b")
	print("C2: c")
	print("C2: Stop")

c1 = coro1()
c2 = coro2()
c1.send(None)
c2.send(None)
print(c1,c2)
print('-'*50)

						


