# 安卓+Termux+FFmpeg 中使用硬件转码时的使用指南

## 前言

本文档基于 **Android + Termux + FFmpeg + 高通芯片** 的实际调试经验整理而成。在移动端使用 hevc_mediacodec 进行硬件转码时，常因参数配置不当、芯片兼容性差异或 FFmpeg 版本限制导致转码失败。本指南旨在提供一套经过验证的参数配置方案、踩坑记录及自动化脚本，帮助开发者在 Android 环境下稳定、高效地完成硬件加速转码任务。

## 目录

1. [背景信息](#一背景信息)
2. [基本命令格式](#二基本命令格式)
3. [关键参数详解](#三关键参数详解)
4. [踩坑记录与解决方案](#四踩坑记录与解决方案)
5. [芯片兼容性说明](#五芯片兼容性说明)
6. [最终可用命令](#六最终可用命令)
7. [推荐的带自动降级重试的 Shell 脚本](#七推荐的带自动降级重试的-shell-脚本)
8. [自动检测 GOP 并转码的一键脚本](#八自动检测-gop-并转码的一键脚本)
9. [调试环境信息](#九调试环境信息)

## 一、背景信息

- **运行环境**：Android + Termux
- **核心工具**：FFmpeg（使用 hevc_mediacodec 硬件编码器）
- **源视频规格**：1080p30，HEVC 编码，MKV 封装，码率约 4337 kb/s
- **设备芯片**：高通（日志标识：`c2.qti.hevc.decoder`）

## 二、基本命令格式

```bash
ffmpeg -hide_banner -hwaccel mediacodec -i input.mkv \
  -c:v hevc_mediacodec [参数] \
  -c:a copy -c:s copy output.mkv
```

### 参数说明

| 参数 | 说明 |
|---|---|
| `-hwaccel mediacodec` | 启用硬件解码加速（**必须放在 -i 之前**） |
| `-c:v hevc_mediacodec` | 使用 MediaCodec 硬件 HEVC 编码器 |
| `-c:a copy` | 音频流直接拷贝，不重编码 |
| `-c:s copy` | 字幕流直接拷贝，不重编码 |

## 三、关键参数详解

### 3.1 GOP 大小（-g）

- **必须设置**，且值应 **≥ 帧率**（如 30fps 时至少 `-g 30`，推荐 `-g 60` 即每 2 秒一个关键帧）。
- 不设置时 FFmpeg 会警告：`please set gop_size properly (>= fps)`。
- 若需与源视频 GOP 一致，需先用 ffprobe 检测：

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries frame=pict_type -of csv=p=0 input.mp4 | \
  awk '/^I/{if(prev!="")print NR-prev; prev=NR}' | \
  awk '{sum+=$1; n++} END{if(n>0) printf "%d", sum/n; else print 60}'
```

**注意**：硬件编码器的 GOP 不一定精确，某些芯片仅近似遵循；若源视频为变 GOP（动态 GOP），固定值无法完全还原原始结构。

### 3.2 Level 参数（-level）

`ffmpeg -h encoder=hevc_mediacodec` 中显示的字符串别名（如 `m6`、`h5.1`）在某些 FFmpeg 版本中不被支持，会报错：

```
Undefined constant or missing '(' in 'm6'
```

**解决方案**：使用对应的 **整数值** 替代字符串别名。

#### 常用 Level 整数值对照表

| Level | 字符串别名 | 整数值 | 适用场景 |
|---|---|---|---|
| 4.0 | m4 | 1024 | 720p30 |
| 4.1 | m4.1 | 4096 | 1080p30（**推荐**） |
| 5.0 | m5 | 16384 | 1080p60 |
| 5.1 | m5.1 | 65536 | 1080p60 高质量 |
| 6.0 | m6 | 1048576 | 4K（很多设备不支持） |

**建议**：1080p30 视频推荐使用 Level 4.1（`4096`）或 5.1（`65536`），不要设太高，否则编码器配置失败。

### 3.3 码率控制模式（-bitrate_mode）

支持三种模式：

| 模式 | 说明 | 兼容性 |
|---|---|---|
| `cq` | 恒定质量 | **最差**，很多芯片不支持，报 `Encoder configure failed, -10000` |
| `vbr` | 可变码率 | **最好**，几乎所有芯片支持，**推荐首选**，配合 `-b:v` 使用 |
| `cbr` | 恒定码率 | 一般，部分芯片支持 |

### 3.4 量化参数（-qp_i_min / -qp_p_min 等）

- 仅在 **CQ 模式** 下需要。
- 数值范围：0–51，越小质量越高、文件越大。
- 1080p 推荐值：**20–28**。
- 包含参数：`qp_i_min`、`qp_i_max`、`qp_p_min`、`qp_p_max`、`qp_b_min`、`qp_b_max`。

### 3.5 码率（-b:v）

- 用于 **VBR/CBR** 模式，指定目标码率。
- 源视频 4337 kb/s 时的推荐值：
  - `-b:v 3M`：更小文件
  - `-b:v 4M`：画质相当
  - `-b:v 6M`：更好画质

### 3.6 像素格式（-pix_fmt）

- 支持：`mediacodec`、`yuv420p`、`nv12`
- **推荐**：`-pix_fmt nv12`，避免不必要的格式转换，提升效率。

## 四、踩坑记录与解决方案

| 坑 | 现象 | 原因 | 解决方案 |
|---|---|---|---|
| **Level 字符串别名不支持** | `[Eval] Undefined constant or missing '(' in 'm6'` | FFmpeg 版本不支持字符串别名 | 改用整数值，如 `-level 1048576` 替代 `-level m6` |
| **Level 值过高** | `Encoder configure failed, -10000` | 芯片硬件编码器不支持该 Level | 降低 Level，1080p30 用 `4096` 或 `65536` |
| **CQ 模式不支持** | 带 `-bitrate_mode cq` 就报 `Encoder configure failed, -10000` | 高通 HEVC 硬件编码器对 CQ 支持不完善 | 换用 VBR：`-bitrate_mode vbr` |
| **GOP 未设置** | `please set gop_size properly (>= fps)` | 未指定 `-g` 参数 | 加上 `-g 60`（30fps 视频） |

## 五、芯片兼容性说明

> **重要提示**：`ffmpeg -h encoder=hevc_mediacodec` 显示的参数列表，仅表示 FFmpeg 层面"支持往编码器里传什么参数"，**不等于你的芯片实际支持这些参数**。

### 调用链路

```
FFmpeg → MediaCodec API → 芯片厂商驱动（高通/联发科/三星...）
```

真正决定参数能否使用的是 **芯片厂商的编码器实现**，每一家的硬件编码器能力不同，驱动实现质量也不同。**必须实际测试才能确认**。

### 各参数兼容性参考表

| 参数 | 兼容性 |
|---|---|
| `-g`（GOP） | 基本通用 |
| `-level` | 取决于芯片支持的 HEVC profile/level 上限 |
| `-bitrate_mode cq` | **兼容性最差**，很多芯片不支持 |
| `-bitrate_mode vbr` | **兼容性最好**，几乎所有芯片支持 |
| `-bitrate_mode cbr` | 兼容性一般 |
| `-qp_i_min` 等 | 取决于芯片是否暴露 QP 控制接口 |
| `-pix_fmt nv12/yuv420p` | 基本通用 |

## 六、最终可用命令

经过完整调试，在高通芯片上最终可用的命令为：

```bash
ffmpeg -hide_banner -hwaccel mediacodec \
  -i input.mkv \
  -c:v hevc_mediacodec -g 60 -level 65536 -bitrate_mode vbr \
  -c:a copy -c:s copy \
  output.mkv
```

如需控制输出码率，可加 `-b:v 4M`：

```bash
ffmpeg -hide_banner -hwaccel mediacodec \
  -i input.mkv \
  -c:v hevc_mediacodec -g 60 -level 65536 -bitrate_mode vbr -b:v 4M \
  -c:a copy -c:s copy \
  output.mkv
```

## 七、推荐的带自动降级重试的 Shell 脚本

```bash
#!/bin/bash
INPUT="$1"
OUTPUT="$2"

# 第一次尝试：VBR + Level 5.1
ffmpeg -hide_banner -hwaccel mediacodec -i "$INPUT" \
  -c:v hevc_mediacodec -g 60 -level 65536 -bitrate_mode vbr -b:v 4M \
  -c:a copy -c:s copy "$OUTPUT" 2>/dev/null

if [ $? -ne 0 ]; then
  echo "第一次尝试失败，降低 Level 重试..."
  ffmpeg -hide_banner -hwaccel mediacodec -i "$INPUT" \
    -c:v hevc_mediacodec -g 60 -level 4096 -bitrate_mode vbr -b:v 4M \
    -c:a copy -c:s copy "$OUTPUT" 2>/dev/null
fi

if [ $? -ne 0 ]; then
  echo "第二次尝试失败，去掉 level 参数重试..."
  ffmpeg -hide_banner -hwaccel mediacodec -i "$INPUT" \
    -c:v hevc_mediacodec -g 60 -b:v 4M \
    -c:a copy -c:s copy "$OUTPUT"
fi
```

## 八、自动检测 GOP 并转码的一键脚本

```bash
#!/bin/bash
INPUT="$1"
OUTPUT="$2"

# 获取源视频 GOP（通过统计关键帧间距）
GOP=$(ffprobe -v error -select_streams v:0 \
  -show_entries frame=pict_type \
  -of csv=p=0 "$INPUT" | \
  awk '/^I/{if(prev!="")print NR-prev; prev=NR}' | \
  awk '{sum+=$1; n++} END{if(n>0) printf "%d", sum/n; else print 60}')

echo "检测到源视频 GOP ≈ $GOP"

ffmpeg -hwaccel mediacodec -i "$INPUT" \
  -pix_fmt nv12 \
  -c:v hevc_mediacodec -b:v 5M -g "$GOP" \
  -c:a copy "$OUTPUT"
```

## 九、调试环境信息

| 项目 | 信息 |
|---|---|
| 操作系统 | Android |
| 终端环境 | Termux |
| FFmpeg 版本 | Lavf62.3.100 |
| 芯片平台 | 高通（c2.qti.hevc） |
| 编码器 | hevc_mediacodec |
| 解码器 | c2.qti.hevc.decoder |

本文档所有命令、参数及脚本均已在上述环境中验证通过，可作为 Android 平台 FFmpeg 硬件转码的参考基准。
