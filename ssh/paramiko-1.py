#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-23 13:58:27
# author calllivecn <c-all@qq.com>


import paramiko

from config import *

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect("localhost",username=USERNAME, password=PASSWORD)

stdin, stdout, stderr = ssh.exec_command("uname -a")

print("stdout:", stdout.read().decode(),"\n","stderr:", stderr.read().decode())
print("退出码：", stdout.channel.recv_exit_status())


stdin, stdout, stderr = ssh.exec_command("named-checkzone {} {}.zone".format("bnq.in","bnq.in"))

print("stdout:",stdout.read().decode(),"\n","stderr:",stderr.read().decode())
print("退出码：", stdout.channel.recv_exit_status())
