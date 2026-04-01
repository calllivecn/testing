

URL="http://10.1.3.1:9000/asr"
AUDIO="audio_2026-03-31_15-13-54.mp3"

# 基础版本 - 自动检测语言
#curl -X POST "$URL" \
#  -F "audio_file=@${AUDIO}" \
#  -F "encode=true" \
#  -F "task=transcribe" \
#  -F "output=txt"

# 指定中文语言
curl -X POST "$URL" \
  -F "audio_file=@${AUDIO}" \
  -F "encode=true" \
  -F "task=transcribe" \
  -F "language=zh" \
  -F "output=txt"

# 获取 JSON 格式结果 (包含时间戳等信息)
#curl -X POST "$URL" \
#  -F "audio_file=@${AUDIO}" \
#  -F "encode=true" \
#  -F "task=transcribe" \
#  -F "language=zh" \
#  -F "output=json"


# 翻译成英文 (task=translate)
#curl -X POST "$URL" \
#  -F "audio_file=@${AUDIO}" \
#  -F "encode=true" \
#  -F "task=translate" \
#  -F "output=txt"
