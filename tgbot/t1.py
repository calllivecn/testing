#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 02:28:37
# author calllivecn <c-all@qq.com>


import json
import asyncio

print("开始bot")

with open("apikey.json") as f:
    apikey = json.load(f)


import asyncio
import telegram


async def main():
    bot = telegram.Bot(apikey["apikey"])
    # 第一步
    async with bot:
        print(await bot.get_me())


    # 第一步
    async with bot:
        await bot.send_message(text='Hi smsbot!', chat_id=6339972957)


if __name__ == '__main__':
    asyncio.run(main())

