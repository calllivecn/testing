#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-26 09:42:40
# author calllivecn <calllivecn@outlook.com>


import pyroute2


def main():

    ip = pyroute2.IPRoute()

    print(ip.get_addr())
