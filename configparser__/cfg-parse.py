#!/usr/bin/env python3
#coding=utf-8
# date 2018-11-08 20:17:20
# author calllivecn <calllivecn@outlook.com>

import configparser

cfg = configparser.ConfigParser()

cfg.read('test.timer', 'utf8')


print("cfg.sections()",cfg.sections())

print("cfg.options()",cfg.options('Timer'))

print("cfg.items()",cfg.items('Unit'))
