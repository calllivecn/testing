# 02_04_combined_test.py
import sys
import time
import random
import asyncio
import threading
import queue
import traceback

import numpy as np
import cv2

from dbus_next.aio import MessageBus
from dbus_next import Variant, BusType

# 导入我们坚如磐石的 PipeWire CFFI 封装
from pipewire_capture import PipeWireCapture

# ================= 全局线程安全队列 =================
# 用于将 PipeWire C 线程的帧数据安全传递给主线程的 OpenCV
frame_queue = queue.Queue(maxsize=2) 

# ================= D-Bus Portal 授权流程 =================
async def request_screencast():
    """
    使用 dbus-next 与 XDG Desktop Portal 交互，获取 PipeWire node_id
    """
    print("🔌 [D-Bus] 正在连接到 Session Bus...")
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    
    # 1. 获取 Portal 代理对象
    introspection = await bus.introspect('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop')
    portal = bus.get_proxy_object('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop', introspection)
    screencast = portal.get_interface('org.freedesktop.portal.ScreenCast')
    
    # 辅助函数：等待 Request 的 Response 信号
    async def wait_for_response(request_path):
        req_introspection = await bus.introspect('org.freedesktop.portal.Desktop', request_path)
        req_obj = bus.get_proxy_object('org.freedesktop.portal.Desktop', request_path, req_introspection)
        req_iface = req_obj.get_interface('org.freedesktop.portal.Request')
        
        future = asyncio.get_event_loop().create_future()
        
        def on_response(response, results):
            if not future.done():
                future.set_result((response, results))
                
        req_iface.on_response(on_response)
        return await future

    # 生成唯一的 handle_token 防止信号串扰
    handle_token = f"py_pw_{random.randint(10000, 99999)}"
    
    try:
        # 2. CreateSession
        print("🔌 [D-Bus] 正在创建 ScreenCast Session...")
        options = {'handle_token': Variant('s', handle_token)}
        request_path = await screencast.call_create_session(options)
        response, results = await wait_for_response(request_path)
        if response != 0: raise Exception(f"CreateSession 失败: {response}")
        
        session_handle = results['session_handle'].value
        print("✅ [D-Bus] Session 创建成功，正在请求选择屏幕...")

        # 3. SelectDevices (1=显示器, 2=窗口, 3=全部)
        options = {
            'types': Variant('u', 1), 
            'multiple': Variant('b', False)
        }
        request_path = await screencast.call_select_devices(session_handle, options)
        response, results = await wait_for_response(request_path)
        if response != 0: raise Exception(f"SelectDevices 失败: {response}")
        
        print("✅ [D-Bus] 设备选择成功，正在启动流 (请观察系统弹窗并点击分享)...")

        # 4. Start
        options = {}
        request_path = await screencast.call_start(session_handle, '', options)
        response, results = await wait_for_response(request_path)
        if response != 0: raise Exception(f"Start 失败或被用户取消: {response}")
        
        # 5. 提取 Node ID
        streams = results['streams'].value
        if not streams: raise Exception("未获取到任何 Stream 节点！")
        node_id = int(streams[0][0])
        print(f"✅ [D-Bus] 授权成功！获取到 PipeWire Node ID: {node_id}")
        
        # 6. 获取 PipeWire FD (注意：dbus-next 对 Unix FD 的支持)
        # OpenPipeWireRemote 返回的是一个 Unix FD
        options = {}
        pw_fd = await screencast.call_open_pipewire_remote(session_handle, options)
        print(f"✅ [D-Bus] 获取到 PipeWire FD: {pw_fd}")
        
        return node_id, pw_fd
        
    except Exception as e:
        print(f"❌ [D-Bus] 授权流程异常: {e}")
        traceback.print_exc()
        return -1, -1
    finally:
        bus.disconnect()

# ================= PipeWire 帧回调 =================
def on_new_frame(data_bytes, size, stride, width, height):
    """
    PipeWire C 线程回调：将 raw bytes 转换为 numpy 数组并推入队列
    """
    try:
        # 推算真实分辨率 (处理 stride padding)
        calc_width = stride // 4 if stride > 0 else width
        calc_height = size // stride if stride > 0 else height
        
        if calc_width <= 0 or calc_height <= 0:
            return

        # 零拷贝映射内存，并裁剪掉 stride 的 padding，去掉第 4 个通道 (x)
        img_bgrx = np.frombuffer(data_bytes, dtype=np.uint8).reshape(calc_height, stride // 4, 4)
        img_bgr = img_bgrx[:calc_height, :calc_width, :3]
        
        # 如果队列满了，丢弃旧帧，保证实时性
        if frame_queue.full():
            try: frame_queue.get_nowait()
            except queue.Empty: pass
            
        frame_queue.put_nowait(img_bgr)
        
    except Exception as e:
        print(f"\n❌ 帧处理异常: {e}")

# ================= 主程序入口 =================
if __name__ == "__main__":
    # 1. 在子线程中运行 asyncio 和 dbus-next 授权流程
    # 这样不会阻塞主线程的 OpenCV 渲染
    db_result = {}
    def run_dbus():
        try:
            db_result['node_id'], db_result['pw_fd'] = asyncio.run(request_screencast())
        except Exception as e:
            print(f"❌ D-Bus 线程崩溃: {e}")
            db_result['node_id'] = -1

    dbus_thread = threading.Thread(target=run_dbus)
    dbus_thread.start()
    
    print("⏳ 等待 D-Bus 授权完成 (请在系统弹窗中操作)...")
    dbus_thread.join() # 等待授权完成
    
    node_id = db_result.get('node_id', -1)
    if node_id < 0:
        print("❌ 未能获取有效的 Node ID，程序退出。")
        sys.exit(1)

    # 2. 初始化 PipeWire 抓帧器
    print("🚀 正在启动 PipeWire 视频流...")
    capture = PipeWireCapture(
        node_id=node_id, 
        on_frame=on_new_frame,
        on_state_change=lambda state: print(f"🔄 PipeWire 状态: {state}")
    )
    capture.start()

    # 3. OpenCV 实时预览循环 (主线程)
    print("🖼️ 正在打开 OpenCV 预览窗口 (按 'q' 或 ESC 退出)...")
    cv2.namedWindow("Wayland PipeWire ScreenCast (dbus-next)", cv2.WINDOW_NORMAL)
    
    frame_count = 0
    last_time = time.time()
    
    try:
        while True:
            try:
                # 从队列中获取最新帧 (超时 10ms，保持 UI 响应)
                img_bgr = frame_queue.get(timeout=0.01)
                cv2.imshow("Wayland PipeWire ScreenCast (dbus-next)", img_bgr)
                frame_count += 1
            except queue.Empty:
                pass # 没有新帧，继续循环
            
            # 计算并打印 FPS
            if time.time() - last_time >= 2.0 and frame_count > 0:
                fps = frame_count / (time.time() - last_time)
                print(f"⏺ 实时抓帧中... FPS: {fps:.1f}    ", end='\r')
                frame_count = 0
                last_time = time.time()
            
            # 处理键盘事件
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 正在清理资源...")
        capture.stop()
        cv2.destroyAllWindows()
        print("👋 程序已安全退出。")
