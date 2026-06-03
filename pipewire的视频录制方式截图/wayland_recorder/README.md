你提出了一个**非常深刻且直击本质**的问题！首先，我必须向你道歉——我上一回合关于“终端必须在后台/前台”的解释是**完全错误**的。那是我在排查时产生的误导。

**你的直觉是对的：命令行进程根本没有“窗口焦点”的概念。** 

为了彻底解开这个谜团，我们先来理清 **Wayland + XDG Portal + PipeWire** 的真实底层机制，然后再看看我们的代码到底卡在了哪里。

---

### 🧠 1. Wayland 屏幕录制的真实机制

在 X11 时代，任何程序都可以随意读取显存截取全屏。但在 Wayland 时代，出于安全考虑，应用被严格隔离（沙盒化），**绝对不能**直接读取其他窗口的画面。

因此，Wayland 引入了 **XDG Desktop Portal** 和 **PipeWire** 的三方协作机制：

1. **XDG Portal (授权中心)**：
   - 你的 Python 脚本通过 D-Bus 告诉 Portal：“我想录屏”。
   - Portal 弹出一个**系统级安全对话框**（这就是你看到的弹窗）。
   - 用户点击“共享”后，Portal 在底层向 PipeWire 守护进程申请创建一个**专属的视频流节点 (Node)**，并把这个 `Node ID` 返回给你的脚本。
   - **关键点**：一旦用户点击共享，授权就成立了。**无论你的 Python 脚本是在前台终端运行，还是在后台作为 systemd 服务运行，授权都是有效的。**

2. **PipeWire (数据管道)**：
   - 你的脚本拿到 `Node ID` 后，作为“消费者”连接到这个节点。
   - 屏幕合成器（如 GNOME 的 Mutter 或 KDE 的 KWin）作为“生产者”，不断把画面帧塞进 PipeWire 管道。
   - **关键点**：只要管道连通，数据就会源源不断地推送过来，**根本不在乎请求数据的进程有没有 GUI 窗口**。

---

### 🔍 2. 为什么我们的流卡在了 `PAUSED`？

既然与窗口焦点无关，那为什么状态变成了 `PAUSED` 就死活不进入 `STREAMING`，也收不到帧呢？

在 PipeWire 中，`PAUSED` 状态意味着：**物理连接已建立，但“格式协商 (Format Negotiation)”未最终达成一致。**

回顾我们的代码，问题出在 `build_video_format_pod` 和连接参数上。Wayland 合成器（生产者）非常“傲娇”，如果我们请求的参数它不支持，它就会拒绝推流：

1. **帧率 (Framerate) 限制过死**：
   我们之前请求的是 `30fps 到 60fps`。但在屏幕共享中，如果画面静止，Wayland 合成器会将帧率降到 0fps 以节省资源。我们限制了 `min_fps=30`，导致合成器觉得“我做不到”，直接拒绝进入 STREAMING。
2. **缺少 SHM (共享内存) 标记**：
   Wayland 默认喜欢用 DMA-Buf（GPU显存直接传输）。但我们是用 Python/CFFI 处理 CPU 内存，必须明确告诉 PipeWire：“我只要 SHM（系统内存）数据”，否则拿到的数据指针在 CPU 端是无效的。

---

# PipeWire 框架捕获 GNOME 桌面屏幕 的完整流程（特别是零拷贝、低延迟的数据流）

```text
Python进程       C适配层          PipeWire守护进程       Mutter(合成器)
   |               |                    |                     |
   |--pw_init...-->|                    |                     |
   |--pw_stream_new>|                    |                     |
   |--add_listener->|                    |                     |
   |               |--pw_stream_connect->|                     |
   |               |                    |--绑定ScreenCast源--->|
   |               |<--param_changed----|                     |
   |<--param_changed(路由到Python)       |                     |
   |               |                    |                     |
   |               |                    |<---写入共享内存------|
   |               |<--process事件------|                     |
   |<--on_stream_process(回调)           |                     |
   |--dequeue_buffer-------------------->|                     |
   |<--返回内存指针+stride                |                     |
   |[Python用memoryview零拷贝处理]        |                     |
   |--queue_buffer---------------------->|                     |
   |               |                    |--继续下一帧-------->|
```


# 📐 一张图看懂数据流向

```text

[ 浏览器窗口 ] 
   │ 以为自己是 2560x1440 (逻辑尺寸)
   ▼
[ GNOME Mutter 窗口管理器 ] 
   │ 乘以缩放比例 (2.0)，在显存中渲染出 5120x2880 的物理像素
   ▼
[ 显存 Frame Buffer ] (真实大小: 5120x2880)
   │
   ├─➡️ [ XDG Portal (D-Bus) ] 提取元数据 ➡️ 返回逻辑尺寸: 2560x1440
   │
   └─➡️ [ PipeWire ] 直接映射显存 ➡️ 协商物理 Buffer: 5120x2880
```
