#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/param/format-utils.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 记录器上下文
struct RecorderContext {
    struct pw_main_loop *loop;
    struct pw_stream *stream;

    // 视频状态
    uint32_t width;
    uint32_t height;
    uint32_t format;
    uint32_t stride;
    int is_valid_format;

    // ========== ✅ 新增：FPS 控制 ==========
    uint32_t target_fps;         // 目标 FPS (0 = 不限制)
    uint32_t frame_interval_ns;  // 帧间隔 (纳秒)
    struct timespec last_frame_time;  // 上一帧时间

    // ========== ✅ 新增：裁剪区域 ==========
    int crop_enabled;
    uint32_t crop_x, crop_y, crop_w, crop_h;

    // ========== ✅ 新增：裁剪缓冲区 ==========
    void *crop_buffer;           // 裁剪后的帧数据缓冲区
    uint32_t crop_buffer_size;   // 缓冲区大小

    // Python 回调
    void *py_userdata;
    void (*py_on_state)(void*, int, int);
    void (*py_on_format)(void*, uint32_t, uint32_t, uint32_t);
    void (*py_on_frame)(void*, void*, uint32_t, uint32_t, uint32_t, uint32_t);
};

// 状态变更回调
static void on_state_changed(void *userdata, int old, int new, const char *error) {
    struct RecorderContext *ctx = userdata;
    if (ctx->py_on_state) ctx->py_on_state(ctx->py_userdata, old, new);
}

// 格式协商回调
static void on_param_changed(void *userdata, uint32_t id, const struct spa_pod *param) {
    struct RecorderContext *ctx = userdata;
    if (!ctx || !param || id != SPA_PARAM_Format) return;

    struct spa_video_info_raw info;
    if (spa_format_video_raw_parse(param, &info) < 0) {
        fprintf(stderr, "[C-Error] 无法解析视频格式\n");
        ctx->is_valid_format = 0;
        pw_stream_set_active(ctx->stream, false);
        return;
    }

    if (info.format != SPA_VIDEO_FORMAT_BGRx &&
        info.format != SPA_VIDEO_FORMAT_RGBx &&
        info.format != SPA_VIDEO_FORMAT_BGRA &&
        info.format != SPA_VIDEO_FORMAT_RGBA) {
        fprintf(stderr, "[C-Error] 不支持的像素格式: %d\n", info.format);
        ctx->is_valid_format = 0;
        pw_stream_set_active(ctx->stream, false);
        return;
    }

    ctx->width = info.size.width;
    ctx->height = info.size.height;
    ctx->format = info.format;
    ctx->stride = SPA_ROUND_UP_N(info.size.width * 4, 4);
    ctx->is_valid_format = 1;

    // ✅ 新增：如果启用了裁剪，验证并分配裁剪缓冲区
    if (ctx->crop_enabled) {
        // 裁剪区域边界检查
        if (ctx->crop_x + ctx->crop_w > ctx->width) {
            fprintf(stderr, "[C-Warn] 裁剪区域超出宽度, 自动修正: %u -> %u\n",
                    ctx->crop_w, ctx->width - ctx->crop_x);
            ctx->crop_w = ctx->width - ctx->crop_x;
        }
        if (ctx->crop_y + ctx->crop_h > ctx->height) {
            fprintf(stderr, "[C-Warn] 裁剪区域超出高度, 自动修正: %u -> %u\n",
                    ctx->crop_h, ctx->height - ctx->crop_y);
            ctx->crop_h = ctx->height - ctx->crop_y;
        }
        if (ctx->crop_x >= ctx->width || ctx->crop_y >= ctx->height ||
            ctx->crop_w == 0 || ctx->crop_h == 0) {
            fprintf(stderr, "[C-Error] 裁剪区域完全无效! 禁用裁剪\n");
            ctx->crop_enabled = 0;
        } else {
            // 分配裁剪缓冲区 (只在格式变更时分配一次)
            uint32_t crop_stride = SPA_ROUND_UP_N(ctx->crop_w * 4, 4);
            ctx->crop_buffer_size = crop_stride * ctx->crop_h;
            ctx->crop_buffer = realloc(ctx->crop_buffer, ctx->crop_buffer_size);
            printf("[C-Info] 裁剪缓冲区已分配: %ux%u, stride=%u, size=%u\n",
                   ctx->crop_w, ctx->crop_h, crop_stride, ctx->crop_buffer_size);
        }
    }

    printf("[C-Info] 格式协商成功: %ux%u, format=%u, stride=%u, crop=%s\n",
           ctx->width, ctx->height, ctx->format, ctx->stride,
           ctx->crop_enabled ? "ON" : "OFF");

    if (ctx->py_on_format) {
        if (ctx->crop_enabled) {
            ctx->py_on_format(ctx->py_userdata, ctx->crop_w, ctx->crop_h, ctx->format);
        } else {
            ctx->py_on_format(ctx->py_userdata, ctx->width, ctx->height, ctx->format);
        }
    }
}

// ========== ✅ 核心：高性能帧处理回调 (含 FPS 丢帧 + 区域裁剪) ==========
static void on_process(void *userdata) {
    struct RecorderContext *ctx = userdata;
    if (!ctx || !ctx->stream || !ctx->is_valid_format) return;

    struct pw_buffer *b = pw_stream_dequeue_buffer(ctx->stream);
    if (!b) return;

    struct spa_buffer *buf = b->buffer;
    if (!buf || buf->n_datas < 1) goto finish;

    struct spa_data *d = &buf->datas[0];

    if (d->data != NULL && d->chunk->size > 0) {

        // ====== 1. FPS 丢帧控制 ======
        if (ctx->target_fps > 0 && ctx->frame_interval_ns > 0) {
            struct timespec now;
            clock_gettime(CLOCK_MONOTONIC, &now);

            uint64_t elapsed_ns =
                (uint64_t)(now.tv_sec - ctx->last_frame_time.tv_sec) * 1000000000ULL +
                (uint64_t)(now.tv_nsec - ctx->last_frame_time.tv_nsec);

            if (elapsed_ns < ctx->frame_interval_ns) {
                // 还不到发送时间，直接丢帧
                goto finish;
            }
            ctx->last_frame_time = now;
        }

        // ====== 2. 获取原始像素数据指针 ======
        void *real_data = SPA_MEMBER(d->data, d->chunk->offset, void);

        // ====== 3. 区域裁剪 (纯 C 指针运算，极高性能) ======
        if (ctx->crop_enabled && ctx->crop_buffer) {
            uint32_t src_stride = ctx->stride;
            uint32_t dst_stride = SPA_ROUND_UP_N(ctx->crop_w * 4, 4);
            uint8_t *src = (uint8_t *)real_data;
            uint8_t *dst = (uint8_t *)ctx->crop_buffer;

            // 起始行偏移
            src += (uint64_t)ctx->crop_y * src_stride + ctx->crop_x * 4;

            // 逐行 memcpy (只拷贝需要的像素列)
            for (uint32_t row = 0; row < ctx->crop_h; row++) {
                memcpy(dst, src, ctx->crop_w * 4);
                src += src_stride;
                dst += dst_stride;
            }

            // 回调：发送裁剪后的数据
            if (ctx->py_on_frame) {
                ctx->py_on_frame(ctx->py_userdata,
                                 ctx->crop_buffer,
                                 ctx->crop_buffer_size,
                                 ctx->crop_w,
                                 ctx->crop_h,
                                 dst_stride);
            }
        } else {
            // 不裁剪：直接传递原始帧
            if (ctx->py_on_frame) {
                ctx->py_on_frame(ctx->py_userdata, real_data,
                                 d->chunk->size, ctx->width, ctx->height, ctx->stride);
            }
        }
    }

finish:
    pw_stream_queue_buffer(ctx->stream, b);
}

// 事件监听器
static const struct pw_stream_events stream_events = {
    PW_VERSION_STREAM_EVENTS,
    .state_changed = on_state_changed,
    .param_changed = on_param_changed,
    .process = on_process,
};

void* create_recorder() {
    pw_init(NULL, NULL);
    struct RecorderContext *ctx = calloc(1, sizeof(struct RecorderContext));
    ctx->loop = pw_main_loop_new(NULL);

    ctx->stream = pw_stream_new_simple(
        pw_main_loop_get_loop(ctx->loop),
        "python-screen-recorder",
        NULL,
        &stream_events,
        ctx
    );
    if (!ctx->stream) {
        fprintf(stderr, "[C-Error] 无法创建 PipeWire 流！\n");
        free(ctx);
        return NULL;
    }
    return ctx;
}

void destroy_recorder(void* userdata) {
    struct RecorderContext *ctx = userdata;
    if (!ctx) return;
    if (ctx->crop_buffer) free(ctx->crop_buffer);
    if (ctx->stream) pw_stream_destroy(ctx->stream);
    if (ctx->loop) pw_main_loop_destroy(ctx->loop);
    free(ctx);
}

void set_callbacks(void* userdata, void* py_userdata, void* on_state, void* on_format, void* on_frame) {
    struct RecorderContext *ctx = userdata;
    ctx->py_userdata = py_userdata;
    ctx->py_on_state = on_state;
    ctx->py_on_format = on_format;
    ctx->py_on_frame = on_frame;
}

// ========== ✅ 设置目标 FPS ==========
void set_target_fps(void* userdata, uint32_t fps) {
    struct RecorderContext *ctx = userdata;
    ctx->target_fps = fps;
    if (fps > 0) {
        ctx->frame_interval_ns = 1000000000ULL / fps;
    } else {
        ctx->frame_interval_ns = 0;
    }
    printf("[C-Info] 目标 FPS 设置为: %u (间隔: %u ns)\n", fps, ctx->frame_interval_ns);
}

// ========== ✅ 设置裁剪区域 ==========
void set_crop_region(void* userdata, int enabled, uint32_t x, uint32_t y, uint32_t w, uint32_t h) {
    struct RecorderContext *ctx = userdata;
    ctx->crop_enabled = enabled;
    ctx->crop_x = x;
    ctx->crop_y = y;
    ctx->crop_w = w;
    ctx->crop_h = h;
    printf("[C-Info] 裁剪区域: enabled=%d, x=%u, y=%u, w=%u, h=%u\n", enabled, x, y, w, h);
}

int connect_stream(void* userdata, uint32_t node_id) {
    struct RecorderContext *ctx = userdata;

    const struct spa_pod *params[1];
    uint8_t buffer[1024];
    struct spa_pod_builder b = SPA_POD_BUILDER_INIT(buffer, sizeof(buffer));

    // ✅ framerate = 0/1 (可变，保证协商成功)
    // ✅ maxFramerate = 目标帧率 (提示服务端限制产出)
    uint32_t fps = ctx->target_fps > 0 ? ctx->target_fps : 60;

    params[0] = spa_pod_builder_add_object(&b,
        SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
        SPA_FORMAT_mediaType,       SPA_POD_Id(SPA_MEDIA_TYPE_video),
        SPA_FORMAT_mediaSubtype,    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
        SPA_FORMAT_VIDEO_format,    SPA_POD_CHOICE_ENUM_Id(5,
                                    SPA_VIDEO_FORMAT_BGRx,
                                    SPA_VIDEO_FORMAT_BGRx,
                                    SPA_VIDEO_FORMAT_RGBx,
                                    SPA_VIDEO_FORMAT_BGRA,
                                    SPA_VIDEO_FORMAT_RGBA),
        SPA_FORMAT_VIDEO_size,      SPA_POD_CHOICE_RANGE_Rectangle(
                                    &SPA_RECTANGLE(1920, 1080),
                                    &SPA_RECTANGLE(1, 1),
                                    &SPA_RECTANGLE(4096, 4096)),
        SPA_FORMAT_VIDEO_maxFramerate,  SPA_POD_CHOICE_RANGE_Fraction(
                                        &SPA_FRACTION(fps, 1),    // 默认
                                        &SPA_FRACTION(1, 1),      // 最小
                                        &SPA_FRACTION(fps, 1)     // 最大=目标FPS
                                        ));
    /*
    推荐方案：framerate=0/1 + maxFramerate + C层丢帧（双保险）
                    ┌──────────────────────────────────┐
                    │  服务端 (合成器 Portal 节点)       │
                    │                                  │
                    │  收到 maxFramerate=5 的请求：     │
                    │                                  │
                    │  Mutter (GNOME):                 │
                    │    可能遵守 → 只产出 ~5fps ✅     │
                    │    可能忽略 → 仍然产出 ~60fps ❌  │
                    │                                  │
                    │  KWin (KDE):                     │
                    │    行为未知，取决于版本           │
                    └──────────┬───────────────────────┘
                               │
                    ┌──────────▼───────────────────────┐
                    │  C层 on_process (双保险)          │
                    │                                  │
                    │  clock_gettime 检查帧间隔         │
                    │  if (elapsed < 200ms) → 丢帧     │
                    │  → 保证精确 5fps 输出到 Python   │
                    └──────────────────────────────────┘
    最好情况：服务端遵守 maxFramerate，从源头减少帧产出 → 合成器少渲染帧，省 GPU/CPU
    最坏情况：服务端忽略 maxFramerate → C 层 on_process 丢帧兜底，功能正确
    */

    return pw_stream_connect(ctx->stream,
                             PW_DIRECTION_INPUT,
                             node_id,
                             PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS,
                             params, 1);
}

void run_loop(void* userdata) {
    struct RecorderContext *ctx = userdata;
    pw_main_loop_run(ctx->loop);
}

void stop_loop(void* userdata) {
    struct RecorderContext *ctx = userdata;
    pw_main_loop_quit(ctx->loop);
}
