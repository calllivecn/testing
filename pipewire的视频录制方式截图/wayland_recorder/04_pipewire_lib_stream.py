#!/usr/bin/env python3
# 04_pipewire_stream.py
import asyncio
import time
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType, Variant, BusType
from pipewire_capture import PipeWireCapture

# ================= 业务层回调 =================
frame_count = 0

def on_frame_received(data, size, stride, width, height):
    global frame_count
    frame_count += 1
    if frame_count == 1:
        print(f"\n🚨 [首帧捕获] 大小: {size} bytes, Stride: {stride}")
    if frame_count % 30 == 0:
        print(f"\r⏺ 成功抓帧: #{frame_count} (Stride: {stride})", end="")

def on_state_changed(state_str):
    print(f"\n🔄 [流状态变更] -> {state_str}")
    if state_str == "STREAMING":
        print("🎉 底层开始推流了！")

# ================= D-Bus Portal 交互 =================
async def main():
    print("="*50)
    print("🔍 联合测试: D-Bus 授权 + 封装好的 PipeWire 库")
    print("="*50)
    
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    sender = bus.unique_name.replace('.', '_').replace(':', '_')[1:]
    
    print("🔹 正在请求屏幕共享授权 (请在弹窗中点击分享)...")
    token = "stream_token"
    session_token = "stream_session_token"
    expected_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
    
    response_event = asyncio.Event()
    node_id_holder = []

    def handler(msg):
        if msg.message_type == MessageType.SIGNAL and msg.interface == 'org.freedesktop.portal.Request' and msg.member == 'Response' and msg.path == expected_path:
            if msg.body[0] == 0:
                streams = msg.body[1].get('streams', Variant('a(ua{sv})', [])).value
                if streams:
                    node_id_holder.append(streams[0][0].value if hasattr(streams[0][0], 'value') else streams[0][0])
            response_event.set()
        return False

    bus.add_message_handler(handler)
    
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='CreateSession', signature='a{sv}', body=[{'session_handle_token': Variant('s', session_token), 'handle_token': Variant('s', 'session_req')}] ))
    session_path = f"/org/freedesktop/portal/desktop/session/{sender}/{session_token}"
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='SelectSources', signature='oa{sv}', body=[session_path, {'types': Variant('u', 1), 'cursor_mode': Variant('u', 1), 'multiple': Variant('b', False), 'handle_token': Variant('s', 'select_req')}] ))
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='Start', signature='osa{sv}', body=[session_path, "", {'handle_token': Variant('s', token)}] ))
    
    await response_event.wait()
    
    if not node_id_holder:
        print("❌ 授权失败或被取消")
        bus.disconnect()
        return
        
    node_id = int(node_id_holder[0])
    print(f"✅ 授权成功! 获取到 Node ID: {node_id}")

    # 🎯 核心：使用封装好的库，代码极其清爽！
    capture = PipeWireCapture(
        node_id=node_id, 
        on_frame=on_frame_received, 
        on_state_change=on_state_changed
    )
    
    print("💡 启动 PipeWire 抓帧...")
    capture.start()

    print("⏳ 录制 10 秒...")
    await asyncio.sleep(10)

    print("\n⏹ 停止录制...")
    capture.stop()
    bus.disconnect()
    
    if frame_count > 0:
        print(f"\n🎉🎉🎉 终极测试通过！成功抓取 {frame_count} 帧！架构完美！")
    else:
        print("\n⚠️ 依然没有抓到帧。")

if __name__ == "__main__":
    asyncio.run(main())
