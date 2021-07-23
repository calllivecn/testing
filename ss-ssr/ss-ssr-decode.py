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

import sys
from pprint import pprint
from base64 import decodebytes, encodebytes, urlsafe_b64decode, urlsafe_b64encode

ssr_address = []
for ssr in sys.argv[1:]:

    if ssr.startswith("ssr://"):
        addr = ssr.lstrip("ssr://")
    elif ssr.startswith("ss://"):
        addr = ssr.lstrip("ss://")

    while len(addr) % 4 != 0:
        addr += "="

    #ssr_addr = decodebytes(addr)
    ssr_addr = urlsafe_b64decode(addr)
    ssr_address.append(ssr_addr)


for info in ssr_address:
    pprint(info.split(b":"))

