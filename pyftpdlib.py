#!/usr/bin/env python3
#coding=utf-8

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

authorizer = DummyAuthorizer()
#authorizer.add_user("user", "12345", "/home/giampaolo", perm="elradfmw")
authorizer.add_anonymous('.')

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.0.0.1", 2121), handler)
server.serve_forever()

