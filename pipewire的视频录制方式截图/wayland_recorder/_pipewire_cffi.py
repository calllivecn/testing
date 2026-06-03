import cffi

ffi = cffi.FFI()

# 1. 定义 C 接口 (给 Python 调用的函数)
ffi.cdef("""
    typedef void (*py_state_cb)(void* userdata, int old_state, int new_state);
    typedef void (*py_format_cb)(void* userdata, uint32_t w, uint32_t h, uint32_t fmt);
    typedef void (*py_frame_cb)(void* userdata, void* data, uint32_t size, uint32_t w, uint32_t h, uint32_t stride);

    void* create_recorder();
    void destroy_recorder(void* ctx);
    
    void set_callbacks(void* ctx, void* userdata, py_state_cb on_state, py_format_cb on_format, py_frame_cb on_frame);
    
    int connect_stream(void* ctx, uint32_t node_id);
    void run_loop(void* ctx);
    void stop_loop(void* ctx);
""")

# 2. 编写 C 源码 (核心底层逻辑)
c_source = """
#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/param/format-utils.h>
#include <stdio.h>
#include <stdlib.h>

// 记录器上下文
struct RecorderContext {
    struct pw_main_loop *loop;
    struct pw_stream *stream;
    
    // 视频状态
    uint32_t width;
    uint32_t height;
    uint32_t format;
    uint32_t stride;
    int is_valid_format; // 标记格式是否协商成功

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

// 格式协商回调 (核心修复点)
static void on_param_changed(void *userdata, uint32_t id, const struct spa_pod *param) {
    struct RecorderContext *ctx = userdata;
    if (!ctx || !param || id != SPA_PARAM_Format) return;

    struct spa_video_info_raw info;
    // 尝试解析 Raw 视频格式
    if (spa_format_video_raw_parse(param, &info) < 0) {
        fprintf(stderr, "[C-Error] 无法解析视频格式 (可能是 DMA-BUF)，拒绝此流！\\n");
        ctx->is_valid_format = 0;
        // 如果格式不支持，直接断开流，防止后续 process 崩溃
        pw_stream_set_active(ctx->stream, false); 
        return;
    }

    // 只支持常见的内存映射格式 (BGRx, RGBx, BGRA, RGBA)
    if (info.format != SPA_VIDEO_FORMAT_BGRx && 
        info.format != SPA_VIDEO_FORMAT_RGBx &&
        info.format != SPA_VIDEO_FORMAT_BGRA && 
        info.format != SPA_VIDEO_FORMAT_RGBA) {
        fprintf(stderr, "[C-Error] 不支持的像素格式: %d\\n", info.format);
        ctx->is_valid_format = 0;
        pw_stream_set_active(ctx->stream, false);
        return;
    }

    ctx->width = info.size.width;
    ctx->height = info.size.height;
    ctx->format = info.format;
    ctx->stride = SPA_ROUND_UP_N(info.size.width * 4, 4); // 确保 4 字节对齐
    ctx->is_valid_format = 1;

    printf("[C-Info] 格式协商成功: %ux%u, format=%u, stride=%u\\n", ctx->width, ctx->height, ctx->format, ctx->stride);
    if (ctx->py_on_format) {
        ctx->py_on_format(ctx->py_userdata, ctx->width, ctx->height, ctx->format);
    }
}

// 数据帧处理回调
// 数据帧处理回调
static void on_process(void *userdata) {
    struct RecorderContext *ctx = userdata;
    if (!ctx || !ctx->stream || !ctx->is_valid_format) return;

    struct pw_buffer *b = pw_stream_dequeue_buffer(ctx->stream);
    if (!b) return;

    struct spa_buffer *buf = b->buffer;
    if (!buf || buf->n_datas < 1) goto finish;

    struct spa_data *d = &buf->datas[0];
    
    // ✅ 修复 1：放宽类型限制。
    // 因为使用了 MAP_BUFFERS，PipeWire 会自动 mmap MemFd，
    // 所以我们只需要检查 d->data 是否被成功映射（不为空）即可。
    if (d->data != NULL && d->chunk->size > 0) {
        if (ctx->py_on_frame) {
            // ✅ 修复 2：极其重要的 SPA_MEMBER 偏移量计算！
            // 真实的像素数据起始地址 = 基础映射地址 + chunk 偏移量
            void *real_data = SPA_MEMBER(d->data, d->chunk->offset, void);
            ctx->py_on_frame(ctx->py_userdata, real_data, d->chunk->size, ctx->width, ctx->height, ctx->stride);
        }
    } else {
        // 调试输出：如果还是没收到，可以取消注释看看 type 到底是什么
        // fprintf(stdout, "[C-Debug] 忽略无效缓冲区 (type=%d, data=%p, size=%u)\\n", d->type, d->data, d->chunk->size);
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

    // ✅ 修复：使用 pw_stream_new_simple 直接绑定到 main_loop
    // 这会自动处理 pw_core 的连接，避免了传入 pw_context 导致的类型不匹配报错
    ctx->stream = pw_stream_new_simple(
        pw_main_loop_get_loop(ctx->loop),
        "python-screen-recorder",
        NULL, // properties
        &stream_events,
        ctx
    );

    if (!ctx->stream) {
        fprintf(stderr, "[C-Error] 无法创建 PipeWire 流！\\n");
        free(ctx);
        return NULL;
    }

    return ctx;
}

void destroy_recorder(void* userdata) {
    struct RecorderContext *ctx = userdata;
    if (!ctx) return;
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

int connect_stream(void* userdata, uint32_t node_id) {
    struct RecorderContext *ctx = userdata;
    
    // 构建支持的格式 Pod (请求 BGRx 和 RGBx)
    const struct spa_pod *params[1];
    uint8_t buffer[1024];
    struct spa_pod_builder b = SPA_POD_BUILDER_INIT(buffer, sizeof(buffer));
    
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
        SPA_FORMAT_VIDEO_framerate, SPA_POD_CHOICE_RANGE_Fraction(
                                    &SPA_FRACTION(60, 1),
                                    &SPA_FRACTION(0, 1),
                                    &SPA_FRACTION(60, 1)));

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
"""

# 3. 编译 C 代码
if __name__ == "__main__":
    ffi.set_source("_pipewire_cffi", c_source, libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])
    ffi.compile(verbose=True)
    print("✅ CFFI 编译成功！")
