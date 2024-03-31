#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-04 11:28:27
# author calllivecn <calllivecn@outlook.com>

from redis.sentinel import Sentinel
sentinel = Sentinel([('localhost', 26379)], socket_timeout=0.1)
sentinel.discover_master("redis-py-test")

