# 测试这个服务怎么样。判断需不需要我自己开发一个类似的。


- hub.docker.com: https://hub.docker.com/r/onerahmet/openai-whisper-asr-webservice
- 文档地址：https://ahmetoner.com/whisper-asr-webservice/
- https://github.com/ahmetoner/whisper-asr-webservice

```shell
docker run -d -p 9000:9000 \
  -e ASR_MODEL=base \
  -e ASR_ENGINE=openai_whisper \
  onerahmet/openai-whisper-asr-webservice:latest
```

- 为了避免重复下载，从而缩短容器启动时间，您可以将缓存目录持久化：

```shell
docker run -d -p 9000:9000 \
  -v $PWD/cache:/root/.cache/ \
```


Key Features  主要特点

Multiple ASR engines support (OpenAI Whisper, Faster Whisper, WhisperX)
支持多种 ASR 引擎（OpenAI Whisper、Faster Whisper、WhisperX）

Multiple output formats (text, JSON, VTT, SRT, TSV)
多种输出格式（文本、JSON、VTT、SRT、TSV）

Word-level timestamps support
支持单词级时间戳

Voice activity detection (VAD) filtering
语音活动检测 (VAD) 滤波

Speaker diarization (with WhisperX)
说话人分割（使用 WhisperX）

FFmpeg integration for broad audio/video format support
FFmpeg 集成，支持多种音频/视频格式

GPU acceleration support
GPU 加速支持

Configurable model loading/unloading
可配置模型装载/卸载

REST API with Swagger documentation
带有 Swagger 文档的 REST API 文档

Environment Variables  环境变量

Key configuration options:
主要配置选项：

ASR_ENGINE: Engine selection (openai_whisper, faster_whisper, whisperx)
ASR_ENGINE ：引擎选择（openai_whisper、faster_whisper、whisperx）
ASR_MODEL: Model selection (tiny, base, small, medium, large-v3, etc.)
ASR_MODEL ：模型选择（微型、基础、小型、中型、大型-v3 等）
ASR_MODEL_PATH: Custom path to store/load models
ASR_MODEL_PATH ：存储/加载模型的自定义路径
ASR_DEVICE: Device selection (cuda, cpu)
ASR_DEVICE ：设备选择（CUDA、CPU）
MODEL_IDLE_TIMEOUT: Timeout for model unloading
MODEL_IDLE_TIMEOUT ：模型卸载超时时间


