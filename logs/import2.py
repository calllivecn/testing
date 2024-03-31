#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-23 16:48:09
# author calllivecn <calllivecn@outlook.com>



from logdir import import1
import logging

#import1.logging.info("这里是import2.py")
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(pathname)s:%(lineno)d] %(message)s",
                    datefmt="%Y-%m-%d-%H:%M:%S")


logging.info("这里是import2.py")
