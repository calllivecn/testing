# 使用playwright + CDP 操作 chrome


- 安装 pip install pytest-playwright


## 使用系统中chrome 打开网页，并录制 python 脚本。

- playwright codegen --channel chrome https://bing.com

- playwright codegen --user-data-dir="$MY_PROFILE_DIR" --channel chrome https://bing.com

## 录制异步版

- playwright codegen --target python-async -o script.py


## 从脚本启动录制。

- play-record-async.py
- play-record.py

- 需要已经启动一个浏览器CDP已经开启。
- 需要第一个标签页为空白。

