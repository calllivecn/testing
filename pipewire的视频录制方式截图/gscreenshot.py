#!/usr/bin/env python3
import asyncio
import os
import sys
import argparse
import shutil
import secrets
from datetime import datetime
from urllib.parse import urlparse, unquote  # 引入 unquote 用于解码中文路径

# pip install dbus-next
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType, Variant

# XDG Desktop Portal 核心元数据
PORTAL_BUS = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
PORTAL_INTERFACE = "org.freedesktop.portal.Screenshot"

class WaylandPortalScreenshotTool:
    def __init__(self):
        self.bus = None

    async def connect(self):
        """初始化连接至 Session Bus"""
        self.bus = await MessageBus().connect()

    async def capture(self, interactive: bool, dest_path: str):
        """
        发起 Portal 截图请求并等待用户在系统弹窗中确认
        """
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        expected_request_path = None

        # 1. 定义信号监听器，捕获 Portal 异步返回的用户操作结果
        def signal_handler(message: Message):
            if (message.message_type == MessageType.SIGNAL and 
                message.interface == "org.freedesktop.portal.Request" and 
                message.member == "Response"):
                
                # 严格匹配当前脚本发起的请求路径
                if expected_request_path and message.path == expected_request_path:
                    response_future.set_result(message.body)
                    self.bus.remove_message_handler(signal_handler)

        # 注册信号监听
        self.bus.add_message_handler(signal_handler)

        # 2. 准备 Portal 配置参数
        token = f"gscreenshot_{secrets.token_hex(4)}"
        options = {
            "interactive": Variant("b", interactive),
            "handle_token": Variant("s", token)
        }

        # 3. 构造并发送 DBus 裸消息
        message = Message(
            destination=PORTAL_BUS,
            path=PORTAL_PATH,
            interface=PORTAL_INTERFACE,
            member="Screenshot",
            signature="sa{sv}",
            body=["", options]
        )

        # 发起调用
        reply = await self.bus.call(message)
        expected_request_path = reply.body[0]
        
        if interactive:
            print("提示: 已拉起系统级截图交互界面，请在弹窗中选择截取范围...")
        else:
            print("提示: 已发起即时全屏捕获，请在系统弹窗中允许访问...")

        # 4. 挂起等待用户操作
        response_code, results = await response_future

        # 5. 处理响应状态码
        if response_code == 1:
            print("错误: 用户拒绝了截图请求或取消了操作。", file=sys.stderr)
            sys.exit(1)
        elif response_code != 0:
            print(f"错误: Portal 异常返回，状态码: {response_code}", file=sys.stderr)
            sys.exit(1)

        # 6. 解析 Portal 返回的临时安全沙盒文件路径并转移
        if "uri" in results:
            uri_str = results["uri"].value
            parsed_url = urlparse(uri_str)
            
            # 【修复核心】使用 unquote 将 %E5%9B%BE%E7%89%87 还原为真实的 “图片” 字样
            decoded_path = unquote(parsed_url.path)
            src_path = os.path.abspath(decoded_path)
            
            if os.path.exists(src_path):
                # 创建目标目录（如果不存在）
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                # 将文件从沙盒缓存目录安全移动到用户指定的输出路径
                shutil.move(src_path, dest_path)
                return dest_path
            else:
                raise FileNotFoundError(f"沙盒文件不存在: {src_path}")
        else:
            raise KeyError("Portal 响应成功但未包含有效的图片 URI 键值。")

def setup_args():
    parser = argparse.ArgumentParser(description="符合 Wayland 安全规范的跨桌面 DBus 异步截图工具")
    parser.add_argument(
        "-i", "--interactive", 
        action="store_true", 
        help="开启交互模式（由系统弹窗提供：选区、截窗口或全屏功能）"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="输出文件的自定义绝对路径 (默认保存至 ~/Pictures)"
    )
    return parser.parse_args()

async def main():
    args = setup_args()
    
    # 规范化输出路径
    if args.output:
        dest_path = os.path.abspath(os.path.expanduser(args.output))
    else:
        pictures_dir = os.path.expanduser("~/Pictures")
        if not os.path.exists(pictures_dir):
            pictures_dir = os.getcwd()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(pictures_dir, f"Portal_Screenshot_{timestamp}.png")

    tool = WaylandPortalScreenshotTool()
    await tool.connect()

    try:
        saved_path = await tool.capture(interactive=args.interactive, dest_path=dest_path)
        print(f"成功！截图已安全转存至: {saved_path}")
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
