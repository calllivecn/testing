## 记录报错


## 只记录视频时正常的。为什么加了音频流播放时就报` [mkv] This is a broken file! Packets with incorrect keyframe flag found. Enabling workaround.`

- MKV 容器的设计：

    ```
    多流（音视频混合）时，播放器必须根据视频流关键帧来同步视频和音频。

    如果关键帧标志不准确：

    MKV 解析器会发现一个非关键帧被当作关键帧，或一个关键帧没标记。

    因此报 [mkv] This is a broken file! Packets with incorrect keyframe flag found，但播放器会启用 workaround 仍然播放。

    也就是说，多流增加了对关键帧标志的依赖，容错机制触发报错提示。
    ```

- 这是一个非常经典且具体的问题。你在 Video-only 模式下正常，加上 Audio 后报错 incorrect keyframe flag，原因在于 PyAV 的 av.Packet 在手动创建时，默认认为不是关键帧，而你没有把音频包标记为关键帧。

### *解决方案*

- 只需要在处理音频包时，显式地将 is_keyframe 设置为 True。



## 报错内容：

- 这个报错HEVC才有，h264不行。
- 播放时，拖动进度条报错：`[ffmpeg/video] hevc: Could not find ref with POC 28`

1. 根本原因：Android 产生的是 Open GOP (CRA 帧)

```
你遇到了 HEVC (H.265) 编码中 Open GOP（开放图像组） 的经典特性。

Closed GOP (IDR 帧): 传统的关键帧。就像一道“铁闸”，切断所有联系。播放器跳到这里，完全不需要看前面的任何内容，直接播放。Seek 完美无报错。
Open GOP (CRA 帧): Android 硬件编码器（HEVC 模式）为了追求高压缩率，默认生成的关键帧通常是 CRA (Clean Random Access) 帧。

特性：CRA 帧本身可以独立解码（所以它被标记为关键帧）。
问题：但紧随 CRA 之后的一两帧（被称为 RASL 帧），在编码设计上允许引用 CRA 之前的画面。
后果：当你 Seek（拖动） 到这个 CRA 帧时，播放器没有“之前的画面”（因为刚跳过来），但接下来的 RASL 帧却伸手要“之前的画面”做参考。 于是 nvdec (NVIDIA 显卡解码器) 就会愤怒地报错：“找不到参考帧 (Ref with POC xx)！”

结论：这不是 PyAV 封装代码的 Bug，而是视频源本身的编码特性。大多数播放器（如 VLC、MPV）遇到这种情况，画面会花一下或卡顿几毫秒，然后自动恢复正常。
```

## *建议：*

- 如果画面能迅速恢复正常，建议忽略此报错。这是硬件解码器过于严谨的日志。