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


app = Flask("echo")

@app.route("/<echo>/")
def hello(echo):
    return f"{echo}\n"

if __name__ == "__main__":
    dirname, filename = os.path.split(sys.argv[0])
    app.config["FLASK_APP"] = filename
    app.config["FLASK_ENV"] = "development"
    app.run(host="0.0.0.0", port=9999, debug=True)
