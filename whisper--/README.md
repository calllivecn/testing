# 目标把 whisper + smail模型，把包成一个fastapi 的 容器


- 安装依赖:

```shell
# 在这之前先使用你常用的工具创建虚拟环境。(uv, virtualenv, python -m venv 等等)

pip install openai-whisper

pip install sounddevice soundfile numpy httpx[http2]
``


# 当前使用先使用这个项目。自己开发先停止。

- https://github.com/xifan2333/fcitx5-vinput