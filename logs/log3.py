#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-15 11:04:58
# author calllivecn <calllivecn@outlook.com>


import logging

handler = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",datefmt="%Y-%m-%d-%H:%M:%S")
handler.setFormatter(fmt)

logger = logging.getLogger("dnsadmin")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


#logging.basicConfig(filename="/tmp/logs-out.log",level=logging.INFO, format="%(asctime)s %(filename)s [line:%(lineno)d] %(message)s", datefmt="%Y-%m-%d")
#logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(filename)s %(module)s [line:%(lineno)d] %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

#logger.debug("test debug",exc_info=True,stack_info=True)
logger.debug("test debug")

logger.info("test info")

logger.warning("test warning")

logger.error("test error")

logger.critical("test crtitcal")

