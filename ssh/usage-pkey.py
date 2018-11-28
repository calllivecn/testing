#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-27 09:34:26
# author calllivecn <c-all@qq.com>

import io

import paramiko

#from config import *
from id_rsa import PKEY

pkey_file = "./id_rsa"

with open(pkey_file) as f:
    fk = io.StringIO(f.read())
    fk.seek(0,io.SEEK_SET)

# pkey = paramiko.RSAKey.from_private_key_file(pkey_file)
# pkey = paramiko.rsakey.RSAKey(key=PKEY)

pkey = paramiko.RSAKey.from_private_key(fk)
fk.close()

paramiko.util.log_to_file("paramiko.log")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('localhost',username="zx",pkey=pkey)

stdin, stdout, stderr = ssh.exec_command("hostnamectl")

print(stdout.read().decode())

