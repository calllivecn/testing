#!/usr/bin/env python3
"""阶段 2: xdg-desktop-portal D-Bus 交互"""
import os
import sys
import asyncio
import random
import string

try:
    from dbus_next.aio import MessageBus
    from dbus_next import Message, MessageType, Variant, BusType
except ImportError:
    sys.exit("❌ 缺少 dbus-next! 请执行: pip install dbus-next")

class PortalSession:
    def __init__(self, bus):
        self.bus = bus
        self.sender = self.bus.unique_name.replace('.', '_').replace(':', '_')[1:]
        self.token_counter = 0
        self.session_handle = None

    def _get_unique_token(self):
        self.token_counter += 1
        return f"pytoken{self.token_counter}"

    async def _call_and_wait(self, method, signature, body):
        token = self._get_unique_token()
        expected_path = f"/org/freedesktop/portal/desktop/request/{self.sender}/{token}"
        
        if isinstance(body[-1], dict):
            body[-1]['handle_token'] = Variant('s', token)

        response_event = asyncio.Event()
        response_data = {}

        def signal_handler(msg):
            if msg.message_type != MessageType.SIGNAL:
                return False
            if (msg.interface == 'org.freedesktop.portal.Request' and 
                msg.member == 'Response' and 
                msg.path == expected_path):
                response_code = msg.body[0]
                if response_code == 0:
                    response_data.update({k: v.value for k, v in msg.body[1].items()})
                response_event.set()
            return False

        self.bus.add_message_handler(signal_handler)
        try:
            msg = Message(
                destination='org.freedesktop.portal.Desktop',
                path='/org/freedesktop/portal/desktop',
                interface='org.freedesktop.portal.ScreenCast',
                member=method, signature=signature, body=body
            )
            reply = await self.bus.call(msg)
            if reply.message_type == MessageType.ERROR:
                raise RuntimeError(f"D-Bus 错误: {reply.error_name}")
            
            await asyncio.wait_for(response_event.wait(), timeout=120.0)
            return response_data
        finally:
            self.bus.remove_message_handler(signal_handler)

    async def get_node_id(self):
        print("🔹 1/3 创建会话...")
        session_token = f"pysession{self.token_counter}"
        res = await self._call_and_wait('CreateSession', 'a{sv}', [{'session_handle_token': Variant('s', session_token)}])
        self.session_handle = res['session_handle']
        print(f"   ✅ 会话建立: {self.session_handle}")

        print("🔹 2/3 选择捕获源 (窗口)...")
        await self._call_and_wait('SelectSources', 'oa{sv}', [
            self.session_handle, 
            {'types': Variant('u', 1), 'cursor_mode': Variant('u', 1), 'multiple': Variant('b', False)}
        ])
        print("   ✅ 捕获源已选择")

        print("🔹 3/3 启动捕获 (请在弹窗中选择窗口并分享)...")
        res = await self._call_and_wait('Start', 'osa{sv}', [self.session_handle, "", {}])
        
        streams = res.get('streams', [])
        if not streams:
            raise RuntimeError("未获取到视频流")
            
        node_id = streams[0][0]
        print(f"   ✅ 授权成功! PipeWire Node ID: {node_id}")
        return int(node_id)

async def test_dbus():
    print("="*40)
    print("🔍 阶段 2: D-Bus Portal 交互测试")
    print("="*40)
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    portal = PortalSession(bus)
    try:
        node_id = await portal.get_node_id()
        print(f"\n🎉 测试通过！获取到 Node ID: {node_id}")
        print("💡 请将此 Node ID 用于下一阶段的 PipeWire 测试。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        bus.disconnect()

if __name__ == "__main__":
    asyncio.run(test_dbus())
