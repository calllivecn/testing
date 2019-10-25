
import asyncio
import aiohttp
import time

start = time.time()

async def get(url):
    session = aiohttp.ClientSession()
    response = await session.get(url)
    result = await response.text()
    session.close()
    return result

async def request():
    url = 'https://www.tmall.com'
    print('Waiting for', url)
    result = await get(url)
    print('Get response from ', url, 'Result len():', len(result))

#tasks = [asyncio.ensure_future(request()) for _ in range(5)]
#loop = asyncio.get_event_loop()
#loop.run_until_complete(asyncio.wait(tasks))

async def main():
    tasks = [asyncio.create_task(request()) for _ in range(5)]
    return await asyncio.gather(*tasks)

asyncio.run(main())

end = time.time()
print('Cost time:', end - start)
