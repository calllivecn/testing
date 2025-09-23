#!/usr/bin/env bash
# Intel iGPU VAAPI / QSV decode/encode test script for ffmpeg

INPUT="${1:-test.mkv}"   # 默认输入文件 test.mkv，支持传参
DEVICE="/dev/dri/renderD128"

echo "=== Step 0: 检查设备和用户组权限 ==="
ls -l $DEVICE
groups | grep -q video || echo "⚠️ 当前用户不在 video 组，可能会导致权限错误"

echo
echo "=== Step 1: 测试 VAAPI 解码 (仅解码丢弃输出) ==="
ffmpeg -hide_banner -hwaccel vaapi -vaapi_device $DEVICE \
    -i "$INPUT" -f null - || echo "❌ VAAPI 解码失败"

echo
echo "=== Step 2: VAAPI 解码 + CPU x264 编码 ==="
ffmpeg -hide_banner -hwaccel vaapi -vaapi_device $DEVICE \
    -i "$INPUT" -vcodec libx264 -preset fast -crf 23 -acodec copy out_vaapi_x264.mp4 || echo "❌ VAAPI 解码 + x264 编码失败"

echo
echo "=== Step 3: VAAPI 解码 + VAAPI 编码 (h264_vaapi) ==="
ffmpeg -hide_banner -vaapi_device $DEVICE -i "$INPUT" \
    -vf 'format=nv12,hwupload' \
    -vcodec h264_vaapi -b:v 4M -acodec copy out_h264_vaapi.mp4 || echo "❌ h264_vaapi 编码失败"

echo
echo "=== Step 4: QSV 解码 (仅解码丢弃输出) ==="
ffmpeg -hide_banner -vcodec hevc_qsv -i "$INPUT" -f null - || echo "❌ QSV 解码失败"

echo
echo "=== Step 5: QSV 解码 + CPU x264 编码 ==="
ffmpeg -hide_banner -vcodec hevc_qsv -i "$INPUT" \
    -vcodec libx264 -preset fast -crf 23 -acodec copy out_qsv_x264.mp4 || echo "❌ QSV 解码 + x264 编码失败"

echo
echo "=== Step 6: QSV 解码 + VAAPI 编码 (实验性) ==="
ffmpeg -hide_banner -vcodec hevc_qsv -i "$INPUT" \
    -vf 'format=nv12,hwupload' \
    -vcodec h264_vaapi -b:v 4M -acodec copy out_qsv_vaapi.mp4 || echo "❌ QSV 解码 + VAAPI 编码失败"

echo
echo "=== 测试完成 ==="

