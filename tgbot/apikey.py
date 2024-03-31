#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 02:37:01
# author calllivecn <calllivecn@outlook.com>

import json

__all__ = ("APIKEY")

with open("apikey.json") as f:
    apikey = json.load(f)


APIKEY = apikey["apikey"]

