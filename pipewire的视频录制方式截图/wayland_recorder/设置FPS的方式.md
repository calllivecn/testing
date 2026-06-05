在`spa_pod_builder`中设置帧率协商通常有四种方式，这取决于你的应用需要的是精准控制，还是对帧率有一定容忍度。

下面是几种常用模式及其对应的`spa_pod_builder`代码示例：

### ✨ 方式一：固定帧率 (最直接)
这种方式适用于**捕获端完全能以精准帧率生成帧**的场景。

```c
// 直接指定一个固定值，例如希望帧率为 30 fps
spa_pod_builder_add(b,
    SPA_FORMAT_VIDEO_framerate,
    SPA_POD_Fraction(&SPA_FRACTION(30, 1)),
    0);
```
*   **核心宏**：`SPA_POD_Fraction` 直接指定一个确切的`spa_fraction`结构。
*   **SPA_FRACTION(30, 1)**：表示分子30，分母1，即30帧/秒。

---

### ✨ 方式二：可变帧率 (向源端表明“我都能接受”)
这种方式表明**你（客户端）愿意接受任何帧率**，甚至包括完全无帧率信息的情况。常用于屏幕捕获，因为你希望以源的原始速度接收帧，而不做额外限制。

```c
// 使用 0/1 来表示 "可变帧率" 或 "接受任意帧率"
spa_pod_builder_add(b,
    SPA_FORMAT_VIDEO_framerate,
    SPA_POD_Fraction(&SPA_FRACTION(0, 1)),
    0);
```
*   **SPA_FRACTION(0, 1)**：这是一种特殊值，表示帧率由数据源决定，你没有任何偏好。

---

### ✨ 方式三：帧率范围 (用于帧率协商)
适用于你的应用可以处理一个范围（例如从15到60帧/秒）的场景。数据源可以在该范围内选择一个最佳值。

```c
// 构建一个范围选项：默认30fps，范围从1fps 到 60fps
spa_pod_builder_add(b,
    SPA_FORMAT_VIDEO_framerate,
    SPA_POD_CHOICE_RANGE_Fraction(
        &SPA_FRACTION(30, 1),   // 默认值
        &SPA_FRACTION(1, 1),    // 最小值
        &SPA_FRACTION(60, 1)    // 最大值
    ),
    0);
```
*   **SPA_POD_CHOICE_RANGE_Fraction**：定义了协商的范围。
*   **参数**：该函数接受三个`spa_fraction`类型的指针，分别对应**默认值**、**最小值**和**最大值**。

---

### ✨ 方式四：使用 `maxFramerate` 组合 (一种特殊用法)
这是一种表达“可以接受任何低于某个上限的帧率”的通用做法。
*   **组合方式**：将`framerate`设为可变（0/1），并使用`SPA_FORMAT_VIDEO_maxFramerate`设置一个范围上限。

```c
// 指示源端可以任意帧率发送，但最高不得超过 60 fps
spa_pod_builder_add(b, SPA_FORMAT_VIDEO_framerate,
    SPA_POD_Fraction(&SPA_FRACTION(0, 1)), 0);
spa_pod_builder_add(b, SPA_FORMAT_VIDEO_maxFramerate,
    SPA_POD_CHOICE_RANGE_Fraction(
        &SPA_FRACTION(60, 1),   // 默认值
        &SPA_FRACTION(1, 1),    // 最小值
        &SPA_FRACTION(60, 1)    // 最大值，表示上限为60fps
    ), 0);
```
*   **效果**：这种写法常见于`xdg-desktop-portal`的实现中，非常适用于你需要限制CPU/GPU或网络带宽使用率的场景。