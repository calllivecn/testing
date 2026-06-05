# libpipewire.py 两种模式的使用对比

## 模式 A：回调模式 (Push) - 适合实时推流、录制

```python
# main_push.py
recorder = PipeWireRecorder()
recorder.set_target_fps(30)

def on_frame(img_bgr, w, h):
    # 每一帧都会触发，处理必须快，否则会阻塞 C 层主循环
    cv2.imshow("Live", img_bgr)
    cv2.waitKey(1)

recorder.set_callbacks(on_frame=on_frame)
recorder.start(node_id, sync_mode=False)

# 主线程等待退出信号
while not recorder.stop_event.is_set():
    time.sleep(0.1)
```

## 模式 B：同步模式 (Pull) - 适合按需截图、CV 分析

```python
# main_sync.py
recorder = PipeWireRecorder()
recorder.set_target_fps(10)

# 启动时指定 sync_mode=True
recorder.start(node_id, sync_mode=True)

print("✅ 已连接，开始同步读取帧...")

while True:
    # 阻塞等待新帧，类似 cap.read()
    result = recorder.read_frame(timeout=3.0)
    
    if result is None:
        print("⚠️ 读取超时或流已断开")
        break
        
    img_bgr, w, h = result
    print(f"📸 拿到一帧: {w}x{h}")
    
    # 这里可以慢慢处理，比如跑 YOLO 推理，不会影响底层 PipeWire
    # 因为 read_frame 总是返回“最新”的那一帧，旧帧会被自动丢弃
    cv2.imwrite("latest.png", img_bgr) 
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

recorder.stop()

```
