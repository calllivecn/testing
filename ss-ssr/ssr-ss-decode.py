#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-04 16:23:26
# https://github.com/calllivecn

"""

在 Base64 编码之前，ss链接的格式是这样的

ss://method:password@server:port


在 Base64 编码之前，ssr 链接的格式是这样的

ssr://server:port:protocol:method:obfs:password_base64/?params_base64
"""

from pprint import pprint
from base64 import decodebytes, encodebytes, urlsafe_b64decode, urlsafe_b64encode

with open('ssr.base64', 'rb') as f:
    base64_file = f.read()



base64_ssr = decodebytes(base64_file)

ssr_address = []
for ssr in base64_ssr.splitlines():

    if ssr.startswith(b"ssr://"):
        addr = ssr.lstrip(b"ssr://")
    elif ssr.startswith(b"ss://"):
        addr = ssr.lstrip(b"ss://")

    while len(addr) % 4 != 0:
        addr += b"="

    #ssr_addr = decodebytes(addr)
    ssr_addr = urlsafe_b64decode(addr)
    ssr_address.append(ssr_addr)


for info in ssr_address:
    pprint(info.split(b":"))


