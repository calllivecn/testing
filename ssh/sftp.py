#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-26 14:07:41
# author calllivecn <c-all@qq.com>

testfile="/tmp/sftp-paramiko.test"

from datetime import datetime

import paramiko

from config import *

transport = paramiko.Transport(("localhost",22))
transport.connect(username=USERNAME, password=PASSWORD)

sftp = paramiko.SFTPClient.from_transport(transport)

# print(sftp.stat(testfile))

try:
    sftp.rename(testfile,testfile+"-{}-error".format(datetime.now()))
except FileNotFoundError:
    print("可能是第一次，没有",testfile)


with sftp.open(testfile,"w+") as f:
    f.write("test paramiko sftp")

sftp.close()