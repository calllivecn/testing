#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-30 11:44:06
# author calllivecn <c-all@qq.com>

from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle)])

if __name__ == '__main__':
    web.run_app(app)
