# PyAv v16.1 使用

## 记录报错

## 只记录视频时正常的。为什么加了音频流播放时就报` [mkv] This is a broken file! Packets with incorrect keyframe flag found. Enabling workaround.`

- MKV 容器的设计：

    ```text
    多流（音视频混合）时，播放器必须根据视频流关键帧来同步视频和音频。

    如果关键帧标志不准确：

    MKV 解析器会发现一个非关键帧被当作关键帧，或一个关键帧没标记。

    因此报 [mkv] This is a broken file! Packets with incorrect keyframe flag found，但播放器会启用 workaround 仍然播放。

    也就是说，多流增加了对关键帧标志的依赖，容错机制触发报错提示。
    ```

- 这是一个非常经典且具体的问题。你在 Video-only 模式下正常，加上 Audio 后报错 incorrect keyframe flag，原因在于 PyAV 的 av.Packet 在手动创建时，默认认为不是关键帧，而你没有把音频包标记为关键帧。

### *解决方案*

- 只需要在处理音频包时，显式地将 is_keyframe 设置为 True。

## 报错内容

- 这个报错HEVC才有，h264不行。
- 播放时，拖动进度条报错：`[ffmpeg/video] hevc: Could not find ref with POC 28`

1. 根本原因：Android 产生的是 Open GOP (CRA 帧)

```text
你遇到了 HEVC (H.265) 编码中 Open GOP（开放图像组） 的经典特性。

Closed GOP (IDR 帧): 传统的关键帧。就像一道“铁闸”，切断所有联系。播放器跳到这里，完全不需要看前面的任何内容，直接播放。Seek 完美无报错。
Open GOP (CRA 帧): Android 硬件编码器（HEVC 模式）为了追求高压缩率，默认生成的关键帧通常是 CRA (Clean Random Access) 帧。

特性：CRA 帧本身可以独立解码（所以它被标记为关键帧）。
问题：但紧随 CRA 之后的一两帧（被称为 RASL 帧），在编码设计上允许引用 CRA 之前的画面。
后果：当你 Seek（拖动） 到这个 CRA 帧时，播放器没有“之前的画面”（因为刚跳过来），但接下来的 RASL 帧却伸手要“之前的画面”做参考。 于是 nvdec (NVIDIA 显卡解码器) 就会愤怒地报错：“找不到参考帧 (Ref with POC xx)！”

结论：这不是 PyAV 封装代码的 Bug，而是视频源本身的编码特性。大多数播放器（如 VLC、MPV）遇到这种情况，画面会花一下或卡顿几毫秒，然后自动恢复正常。
```

- 还是这个问题，感觉不是这样有新说明：

```text
既然你的视频流中包含 B 帧（MediaCodec 产生的），那么处理时间戳（PTS/DTS）的逻辑就必须非常严谨。
核心问题：
有 B 帧意味着 P T S ≠ D T S PTS  =DTS 。
PTS (显示时间)：是非单调的（例如：0, 66, 33... 先显示第1帧，再显示第3帧，最后显示第2帧）。
DTS (解码时间)：必须是严格单调递增的（例如：0, 33, 66...）。
MediaCodec 的特性：它输出的数据顺序就是 DTS 顺序（也就是解码顺序），但它只给你 PTS。
冲突点：如果你简单的设置 dts = pts，对于 B 帧来说，DTS 就会发生“时间倒流”，这是非法的。如果你设置 dts = 严格递增，可能会出现 DTS > PTS 的情况（即解码时间晚于显示时间），这也是非法的。
解决方法：
你需要手动生成一个单调递增的 DTS，并且为了容纳 B 帧，通常需要给 PTS 加上一个延迟偏移量（Offset），以确保永远满足 
D T S ≤ P T S DTS≤PTS 。

```

## *建议：*

- 如果画面能迅速恢复正常，建议忽略此报错。这是硬件解码器过于严谨的日志。

## 好消息是：音频的时间戳处理比视频简单得多

- 1. 音频与视频处理的区别

    | 特性 | 视频 (Video) | 音频 (Audio, AAC) |
    | :-----: | :-------------: | :-----------------: |
    | DTS vs PTS | 可能不同 (如有B帧) | 永远相同 (DTS = PTS) |
    | 单位 | 帧 (Frame) | 采样点 (Sample) |
    | TimeBase | 建议 1/90000 | 建议 1/采样率 (如 1/44100) |
    | Duration | 1/FPS (例如 3000) | 1024 (AAC 固定帧大小) |

## mkv 容器的坑

## 在输出到mkv 容器时。time_base 只会是 Fraction(1, 1000)，你自己在设置 pts dts 时。只能是以 1/1000 为时间基。

## 坑：手动构造 Packet 时，FFmpeg 不会自动转换基准。 当使用 v_ctx.parse(raw_data) 时又会自动转换基准。

    ```text
    对于音频流，请继续保持 time_base = 1 / sample_rate (例如 1/44100)，不要改成 1/1000。
    为什么音频不能用 1/1000？ 这涉及到**精度丢失（Precision Loss）**的问题。
    视频：
    30 FPS = 每帧 33.33ms。
    MKV 用 1ms 的精度记录（33ms, 33ms, 34ms...）。
    虽然有微小误差，但每一帧是一个独立的图片，播放器按大概时间显示即可，肉眼看不出 0.3ms 的抖动。
    音频：
    44100 Hz，一帧 AAC (1024 采样) = 1024 / 44100 ≈ 23.21995
    如果你强制用 1/1000 (1ms) 的单位：
    你只能把 PTS 设为 23。
    误差：丢掉了 0.21995 ms。
    累积后果：播放 5 秒钟（约 215 帧）后，累积误差就会达到 215 × 0.22 ≈ 47 ms
    后果：你的音频会比视频慢，或者出现爆音/卡顿（因为播放器发现采样点不够填满时间轴）。
    正确的做法
    视频：使用 1/1000 (顺应 MKV 的容器特性)。
    音频：使用 1/44100 (顺应音频的物理特性)。
    PyAV/FFmpeg 的 MKV Muxer 非常聪明：
    它允许视频轨道使用 1/1000 的时间基，同时允许音频轨道使用 1/44100 的时间基。它们可以在同一个文件中和平共处。
    ```



---

# 查看 extradata 的前几个字节

- ffprobe -v error -select_streams v:0 -show_entries stream=extradata -of default=noprint_wrappers=1 test.mkv

