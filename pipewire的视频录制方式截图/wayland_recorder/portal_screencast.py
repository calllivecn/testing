"""Portal ScreenCast 异步模块 (保持会话存活)"""
import asyncio
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType, Variant, BusType

class PortalScreenCast:
    def __init__(self):
        self.bus = None
        self.sender = None
        self.session_handle = None
        self.node_id = None
        self._token_counter = 0

        # ✅ 裁剪/窗口尺寸信息（供 PipeWire 层使用）
        self.crop_x = 0
        self.crop_y = 0
        self.crop_w = 0
        self.crop_h = 0
        self.is_window = False

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

    async def start(self):
        """发起屏幕共享请求并阻塞等待用户授权，返回 Node ID"""
        print("🔹 [Portal] 连接 D-Bus 会话总线...")
        self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
        self.sender = self.bus.unique_name.replace('.', '_').replace(':', '_')[1:]

        print("🔹 [Portal] 1/3 创建会话...")
        session_token = f"pysession{self._token_counter}"
        res = await self._call_and_wait('CreateSession', 'a{sv}', [
            {'session_handle_token': Variant('s', session_token)}
        ])
        self.session_handle = res['session_handle']

        print("🔹 [Portal] 2/3 配置捕获源选项...")
        await self._call_and_wait('SelectSources', 'oa{sv}', [
            self.session_handle,
            {
                'types': Variant('u', 3),        # 1=屏幕 | 2=窗口
                'cursor_mode': Variant('u', 2),   # 2=EMBEDDED 鼠标嵌入画面
                'multiple': Variant('b', False)    # 单选
            }
        ])

        print("🔹 [Portal] 3/3 启动捕获 (请在弹窗中选择屏幕或窗口，并点击共享)...")
        res = await self._call_and_wait('Start', 'osa{sv}', [self.session_handle, "", {}])
        streams = res.get('streams', [])
        if not streams:
            raise RuntimeError("未获取到视频流")
        self.node_id = int(streams[0][0])

        # 解析用户选择
        properties = streams[0][1]
        source_type = properties.get('source_type', Variant('u', 0)).value

        # 重置裁剪参数
        self.crop_x = 0
        self.crop_y = 0
        self.crop_w = 0
        self.crop_h = 0
        self.is_window = False

        if source_type == 1:
            choice_str = "整个屏幕 🖥️"
        elif source_type == 2:
            # ✅ 修复：窗口模式下正确标记 is_window = True
            self.is_window = True

            # 🎯 获取窗口在 PipeWire 画布中的偏移量 (x, y)
            pos_variant = properties.get('position')
            if pos_variant:
                self.crop_x, self.crop_y = pos_variant.value

            # 🎯 获取窗口的真实物理尺寸 (width, height)
            size_variant = properties.get('size')
            if size_variant:
                self.crop_w, self.crop_h = size_variant.value

            print(f"✂️ [Portal] 检测到窗口共享模式！")
            print(f"   ➡️ 窗口在画布中的偏移: X={self.crop_x}, Y={self.crop_y}")
            print(f"   ➡️ 窗口真实物理尺寸: {self.crop_w}x{self.crop_h}")
            print(f"   💡 录制时将自动裁剪掉多余的阴影和边框！")
            choice_str = "应用窗口 🪟"
        else:
            choice_str = f"未知类型 ({source_type})"

        print(f"✅ [Portal] 授权成功! 用户选择了: {choice_str} (Node ID: {self.node_id})")
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
