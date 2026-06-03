#!/usr/bin/env python3
import subprocess
import json
import sys
import os
from pathlib import Path

def get_window_geometry():
    """通过交互式工具获取目标窗口的屏幕坐标区域（含装饰的完整几何区域）"""
    try:
        # 使用 slurp 交互选择窗口（用户点击目标窗口）
        result = subprocess.run(
            ["slurp", "-f", "%{x},%{y} %{w}x%{h}"],
            capture_output=True,
            text=True,
            check=True
        )
        geometry = result.stdout.strip()
        if not geometry:
            raise RuntimeError("未选择窗口")
        return geometry
    except FileNotFoundError:
        raise RuntimeError("未安装 'slurp' 工具。请安装：sudo apt install slurp (Debian/Ubuntu) 或 sudo pacman -S slurp (Arch)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"窗口选择失败: {e.stderr}")

def record_window(geometry, output_file="recording.mp4"):
    """调用 wf-recorder 录制指定区域的视频"""
    try:
        # 检查 wf-recorder 是否支持区域捕获
        version_check = subprocess.run(
            ["wf-recorder", "--help"],
            capture_output=True,
            text=True
        )
        if "-g" not in version_check.stdout:
            raise RuntimeError("wf-recorder 版本过低，请升级至 0.4.0+")

        # 执行录制（自动处理音频捕获）
        cmd = [
            "wf-recorder",
            "-g", geometry,  # 指定窗口区域
            "-f", output_file,
            "-a"  # 捕获系统音频（可选，若不需要可移除）
        ]
        print(f"▶ 开始录制窗口区域: {geometry}\n  按 Ctrl+C 停止录制...")
        subprocess.run(cmd, check=True)
        print(f"\n✅ 录制完成! 保存至: {Path(output_file).resolve()}")
    except FileNotFoundError:
        raise RuntimeError("未安装 'wf-recorder'。请安装：sudo apt install wf-recorder (Debian/Ubuntu) 或 sudo pacman -S wf-recorder (Arch)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"录制失败: {e.stderr}")

def main():
    print("🔍 步骤 1: 选择要录制的窗口（点击目标窗口）")
    try:
        geometry = get_window_geometry()
        print(f"  选定窗口区域: {geometry}")
        
        print("\n🔍 步骤 2: 开始录制（按 Ctrl+C 停止）")
        record_window(geometry)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 检查 Wayland 环境
    if os.getenv("XDG_SESSION_TYPE") != "wayland":
        print("❌ 错误: 必须在 Wayland 会话中运行!", file=sys.stderr)
        sys.exit(1)
    
    main()
