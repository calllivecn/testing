#!/usr/bin/env python3
# coding=utf-8
# date 2023-04-14 21:21:20
# author calllivecn <c-all@qq.com>

import os

from locust import (
    FastHttpUser,
    HttpUser,
    task,
    )


#class HttpEcho(HttpUser):
class HttpEcho(FastHttpUser):

    data = os.urandom(512)

    @task
    def calllivecn(self):
        self.client.get("/calllivecn", timeout=60)
        # self.client.post("/post", data=self.data, timeout=60)
