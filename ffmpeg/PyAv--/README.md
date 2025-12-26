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

