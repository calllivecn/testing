#!/usr/bin/env python3
# coding=utf-8
# date 2021-01-25 16:36:35
# author calllivecn <c-all@qq.com>



import sys
from urllib import (
                    request,
                    parse,
                    )



passwd_mgr = request.HTTPPasswordMgrWithDefaultRealm()

#top_level_url = "http://localhost:6789"

top_level_url = sys.argv[1]

#passwd_mgr.add_password(None, top_level_url, username, password)
passwd_mgr.add_password(None, top_level_url, sys.argv[2], sys.argv[3])

handler = request.HTTPBasicAuthHandler(passwd_mgr)

opener = request.build_opener(handler)

#opener.open(top_level_url)

request.install_opener(opener)

headers = {
        "User-Agent": "calllivecn/0.1.12",
        }

req = request.Request(top_level_url, headers=headers)

print("request headers: ", req.headers, sep="\n")

r = request.urlopen(req)

print("response headers: ", r.headers, sep="\n")
print(r.read().decode())
