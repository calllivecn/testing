"""
没有任务数量上限的限制。
"""


import asyncio




async def small_task(loop, delay: int = 1, name=1):
    c = 0

    # for i in range(10):
    while loop.is_running():

        print(f"{name=} delay: {c}")
        await asyncio.sleep(1)
        c += 1

    print(f"{name=} 我结束了.")


async def main():
    loop = asyncio.get_running_loop()
    task_count = 0
    while True:
        task_count += 1
        asyncio.create_task(small_task(loop, delay=1, name=task_count))

        if task_count % 10 == 0:
            print(f"当前并发task数: {task_count=}")
            break

        await asyncio.sleep(0.5)
    

    # 让loop一直运行
    loop_wait = loop.create_future()
    await loop_wait
    

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
