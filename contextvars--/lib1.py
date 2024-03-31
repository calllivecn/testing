#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-02 06:37:38
# author calllivecn <calllivecn@outlook.com>

__all__ = ("server")

import contextvars

server = contextvars.ContextVar("plugin server")


