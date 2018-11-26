#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-23 16:47:10
# author calllivecn <c-all@qq.com>

import logging


#logging.basicConfig(filename="/tmp/logs-out.log",level=logging.INFO, format="%(asctime)s %(filename)s [line:%(lineno)d] %(message)s", datefmt="%Y-%m-%d")
logging.basicConfig(level=logging.DEBUG, 
                    format="%(asctime)s %(filename)s %(module)s [line:%(lineno)d] %(message)s", 
                    datefmt="%Y-%m-%d-%H:%M:%S")

logging.debug("test debug")

logging.info("test info")

logging.warning("test warning")

logging.error("test error")

logging.critical("test crtitcal")

