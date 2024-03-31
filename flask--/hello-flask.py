#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-19 16:42:58
# author calllivecn <calllivecn@outlook.com>

import os
import sys

from flask import (
        Flask,
        )

from werkzeug.routing import BaseConverter


app = Flask("hello")

RAND = os.urandom(54000)

@app.route("/hello/<name>/")
def hello(name):
    return f"hello {name}\n"

@app.route("/rand/")
def rand():
    return RAND

class RegexConver(BaseConverter):
    def __init__(self, url_map, regex):
        # 将正则表达式的参数保存到对象属性中
        # flask会使用这个属性来进行路由的正则匹配
        super().__init__(url_map)
        self.regex = regex

app.url_map.converters["re"] = RegexConver

@app.route("/<re('.*'):string>/")
def tt(string):
    print(string)
    return ""

if __name__ == "__main__":
    dirname, filename = os.path.split(sys.argv[0])
    #os.putenv("FLASK_APP", filename)
    #os.putenv("FLASK_ENV", "development")
    app.config["FLASK_APP"] = filename
    app.config["FLASK_ENV"] = "development"
    app.run(host="0.0.0.0", port=9999, debug=True)
