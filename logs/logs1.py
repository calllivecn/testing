#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-14 22:36:20
# author calllivecn <c-all@qq.com>


import sys

import logging


if len(sys.argv) == 1:
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(filename)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
elif sys.argv[1] == "debug":
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s %(levelname)s %(filename)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
elif sys.argv[1] == "warning":
    logging.basicConfig(level=logging.WARNING,format="%(asctime)s %(levelname)s %(filename)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
else:
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(filename)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    


logging.debug(f"这是 debug 消息")
logging.info(f"这是 info 消息")
logging.warning(f"这是 warning 消息")




