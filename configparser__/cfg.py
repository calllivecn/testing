#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-09 16:08:18
# author calllivecn <c-all@qq.com>


import logging
import configparser
from pprint import pprint


cfg = configparser.ConfigParser()

cfg.read('refresh4autopilot.ini')

for section in cfg.sections():
    print("section",section)
    pprint(cfg.items(section))

