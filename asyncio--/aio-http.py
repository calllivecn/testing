
import asyncio
import aiohttp
import time


async def get(url):
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        result = await response.text()

    return result

async def request():
    url = 'https://www.tmall.com'
    print('等待请求返回：', url)
    result = await get(url)
    print('从', url, '接收的数据长度:', len(result))

async def main():
    for i in range(5):
        task = asyncio.create_task(request())
        await task

start = time.time()

asyncio.run(main())

end = time.time()
print('Cost time:', end - start)
