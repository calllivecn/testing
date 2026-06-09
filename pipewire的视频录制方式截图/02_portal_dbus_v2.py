"""Portal ScreenCast 异步模块 (支持 restore_token 持久化授权)"""
import asyncio

from dbus_next.aio.message_bus import MessageBus
from dbus_next import Message
from dbus_next.signature import Variant
from dbus_next.constants import MessageType, BusType


class PortalScreenCast:
    def __init__(self):
        self.bus = None
        self.sender = None
        self.session_handle = None
        self.node_id = None
        self.restore_token = None          # 保存本次会话获得的 token
        self._token_counter = 0

    def _get_unique_token(self):
        self._token_counter += 1
        return f"pytoken{self._token_counter}"

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
                else:
                    response_data['error'] = response_code
                response_event.set()
                return False

        self.bus.add_message_handler(signal_handler)
        try:
            msg = Message(
                destination='org.freedesktop.portal.Desktop',
                path='/org/freedesktop/portal/desktop',
                interface='org.freedesktop.portal.ScreenCast',
                member=method,
                signature=signature,
                body=body
            )
            reply = await self.bus.call(msg)
            if reply.message_type == MessageType.ERROR:
                raise RuntimeError(f"D-Bus 错误: {reply.error_name}")

            await asyncio.wait_for(response_event.wait(), timeout=120.0)
            if 'error' in response_data:
                raise RuntimeError(f"Portal 拒绝授权 (Code: {response_data['error']})")
            return response_data
        finally:
            self.bus.remove_message_handler(signal_handler)

    async def start(self, restore_token: str = None):
        """
        发起屏幕共享请求并阻塞等待用户授权，返回 Node ID。
        若提供有效的 restore_token，则尝试恢复之前的授权，跳过用户交互。
        """
        print("🔹 [Portal] 连接 D-Bus 会话总线...")
        self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
        self.sender = self.bus.unique_name.replace('.', '_').replace(':', '_')[1:]

        print("🔹 [Portal] 1/3 创建会话...")
        session_token = f"pysession{self._token_counter}"

        # --- 步骤 1：CreateSession 只需要 session_handle_token ---
        create_options = {
            'session_handle_token': Variant('s', session_token)
        }
        res = await self._call_and_wait('CreateSession', 'a{sv}', [create_options])
        self.session_handle = res['session_handle']

        print("🔹 [Portal] 2/3 选择捕获源 (窗口)...")

        # --- 步骤 2：在 SelectSources 阶段传入 persist_mode 和 restore_token ---
        # 定义选择源的选项
        # persist_mode 选项定义授权的持久化级别:
        #   0: 不持久化 (默认行为，不返回 restore_token)
        #   1: 会话/应用级别持久化
        #   2: 永久持久化 (直到用户明确在系统设置中撤销)
        select_options = {
            'types': Variant('u', 1),
            'cursor_mode': Variant('u', 1),
            'multiple': Variant('b', False),
            'persist_mode': Variant('u', 2)  # 2 表示永久记住授权
        }

        # 核心修正：在这里传入之前保存的 token
        if restore_token:
            select_options['restore_token'] = Variant('s', restore_token)
            print(f"🔹 [Portal] 检测到并应用 restore_token: {restore_token}")

        await self._call_and_wait('SelectSources', 'oa{sv}', [
            self.session_handle,
            select_options
        ])

        print("🔹 [Portal] 3/3 启动捕获 (若已恢复则自动继续)...")
        # 如果 restore_token 验证成功，调用 Start 将直接跳过弹窗
        res = await self._call_and_wait('Start', 'osa{sv}', [self.session_handle, "", {}])

        streams = res.get('streams', [])
        if not streams:
            raise RuntimeError("未获取到视频流")

        self.node_id = int(streams[0][0])

        # --- 步骤 3：获取并更新一次性 Token ---
        new_token = res.get('restore_token')
        if new_token:
            self.restore_token = new_token
            print(f"📌 [Portal] 获得新的 restore_token: {self.restore_token}")

        print(f"✅ [Portal] 授权成功! 保持会话存活中... (Node ID: {self.node_id})")
        return self.node_id

    async def stop(self):
        """优雅关闭 Portal 会话"""
        if self.session_handle and self.bus:
            print("🧹 [Portal] 正在关闭屏幕共享会话...")
            try:
                msg = Message(
                    destination='org.freedesktop.portal.Desktop',
                    path=self.session_handle,
                    interface='org.freedesktop.portal.Session',
                    member='Close',
                    signature=''
                )
                await self.bus.call(msg)
            except Exception:
                pass
        if self.bus:
            self.bus.disconnect()



import json
async def main():
    # 尝试读取之前保存的 token
    saved_token = None
    try:
        with open('portal_token.json', 'r') as f:
            saved_token = json.load(f)['restore_token']
    except FileNotFoundError:
        print("没有已保存的token")

    portal = PortalScreenCast()
    try:
        # 传入旧的 restore_token 尝试恢复
        node_id = await portal.start(restore_token=saved_token)
        print(f"捕获流节点 ID: {node_id}")

        print(f"{saved_token=}")
        print(f"{portal.restore_token=}")
        # 保存本次获得的新 token
        if portal.restore_token:
            with open('portal_token.json', 'w') as f:
                json.dump({'restore_token': portal.restore_token}, f)

        # 保持运行……
        await asyncio.sleep(10)
    finally:
        await portal.stop()


if __name__ == "__main__":
    asyncio.run(main())

