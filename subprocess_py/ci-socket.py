#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-06 16:24:53
# author calllivecn <c-all@qq.com>

import sys
import socket
import shlex
import subprocess

def run(sock, cmd):
    p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sock.
