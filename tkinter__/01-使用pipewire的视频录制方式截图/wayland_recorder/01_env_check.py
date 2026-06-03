#!/usr/bin/env python3
"""阶段 1: 环境与依赖检查"""
import os
import sys
import shutil
import ctypes
import subprocess

def check_environment():
    print("="*40)
    print("🔍 阶段 1: 环境与依赖检查")
    print("="*40)
    errors = []

    # 1. 检查 Wayland
    session_type = os.getenv("XDG_SESSION_TYPE", "").lower()
    if session_type != "wayland":
        errors.append(f"❌ 当前会话类型是 '{session_type}'，必须在 Wayland 下运行！")
    else:
        print("✅ Wayland 会话检测通过")

    # 2. 检查桌面环境
    desktop = os.getenv("XDG_CURRENT_DESKTOP", "")
    print(f"ℹ️ 当前桌面环境: {desktop}")
    if not desktop:
        print("⚠️ 警告: XDG_CURRENT_DESKTOP 未设置，可能导致 Portal 无法弹窗")

    # 3. 检查 Python 依赖
    try:
        import dbus_next
        print("✅ Python 依赖: dbus-next 已安装")
    except ImportError:
        errors.append("❌ 缺少 dbus-next，请执行: pip install dbus-next")

    try:
        import av
        print("✅ Python 依赖: PyAV 已安装")
    except ImportError:
        errors.append("❌ 缺少 PyAV，请执行: pip install av")

    # 4. 检查 PipeWire C 库
    try:
        libpw = ctypes.CDLL("libpipewire-0.3.so.0")
        print("✅ 系统依赖: libpipewire-0.3.so.0 加载成功")
    except OSError:
        errors.append("❌ 找不到 libpipewire-0.3.so.0，请安装: sudo apt install libpipewire-0.3-dev")

    # 5. 检查 Portal 进程
    try:
        result = subprocess.run(["pgrep", "-f", "xdg-desktop-portal"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 系统进程: xdg-desktop-portal 正在运行")
        else:
            errors.append("❌ xdg-desktop-portal 进程未运行")
    except Exception as e:
        print(f"⚠️ 无法检查 Portal 进程: {e}")

    print("="*40)
    if errors:
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("🎉 所有环境检查通过！可以进入下一阶段。")

if __name__ == "__main__":
    check_environment()
