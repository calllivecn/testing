# 使用playwright + CDP 操作 chrome


- 安装 pip install pytest-playwright


## 使用系统中chrome 打开网页，并录制 python 脚本。

- playwright codegen --channel chrome https://bing.com

- playwright codegen --user-data-dir="$MY_PROFILE_DIR" --channel chrome https://bing.com

