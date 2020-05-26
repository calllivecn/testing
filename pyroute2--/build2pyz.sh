#!/bin/bash
# date 2020-05-26 09:43:26
# author calllivecn <c-all@qq.com>

cwd=$(dirname $0)

TMP=$(mktemp -d -p "$cwd")

pip3 install --no-compile --target "$TMP" pyroute2

cp -v test.py "$TMP"

python3 -m zipapp -c -o test.pyz -m "test:main" "$TMP"


rm -rf "$TMP"
