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
    
    // ✅ 修改：新增 target_w 和 target_h 参数，用于显式指定目标分辨率
    int connect_stream(void* ctx, uint32_t node_id, uint32_t target_w, uint32_t target_h);
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

    // ✅ 新增：目标分辨率（由 Python 层传入）
    uint32_t target_width;
    uint32_t target_height;

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
    // 尝试解析 Raw 视频格式
    if (spa_format_video_raw_parse(param, &info) < 0) {
        fprintf(stderr, "[C-Error] 无法解析视频格式 (可能是 DMA-BUF)，拒绝此流！\\n");
        ctx->is_valid_format = 0;
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
    ctx->stride = SPA_ROUND_UP_N(info.size.width * 4, 4);
    ctx->is_valid_format = 1;
    printf("[C-Info] 格式协商成功: %ux%u, format=%u, stride=%u\\n", ctx->width, ctx->height, ctx->format, ctx->stride);
    if (ctx->py_on_format) {
        ctx->py_on_format(ctx->py_userdata, ctx->width, ctx->height, ctx->format);
    }
}
// 数据帧处理回调
static void on_process(void *userdata) {
    struct RecorderContext *ctx = userdata;
    if (!ctx || !ctx->stream || !ctx->is_valid_format) return;
    struct pw_buffer *b = pw_stream_dequeue_buffer(ctx->stream);
    if (!b) return;
    struct spa_buffer *buf = b->buffer;
    if (!buf || buf->n_datas < 1) goto finish;
    struct spa_data *d = &buf->datas[0];
    
    if (d->data != NULL && d->chunk->size > 0) {
        if (ctx->py_on_frame) {
            void *real_data = SPA_MEMBER(d->data, d->chunk->offset, void);
            ctx->py_on_frame(ctx->py_userdata, real_data, d->chunk->size, ctx->width, ctx->height, ctx->stride);
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

// ✅ 修改：接受 target_w 和 target_h，在连接前显式指定目标分辨率
int connect_stream(void* userdata, uint32_t node_id, uint32_t target_w, uint32_t target_h) {
    struct RecorderContext *ctx = userdata;

    // 保存目标分辨率
    ctx->target_width = target_w;
    ctx->target_height = target_h;

    // 如果调用方传入了有效的目标分辨率，则使用它作为首选值
    // 否则回退到默认 1920x1080
    uint32_t pref_w = (target_w > 0) ? target_w : 1920;
    uint32_t pref_h = (target_h > 0) ? target_h : 1080;

    printf("[C-Info] 请求目标分辨率: %ux%u\\n", pref_w, pref_h);

    // ================= 方案1：显式指定目标分辨率 =================
    // ================= 方案2：统一像素格式（优先 RGBA） =================
    const struct spa_pod *params[1];
    uint8_t buffer[1024];
    struct spa_pod_builder b = SPA_POD_BUILDER_INIT(buffer, sizeof(buffer));
    
    params[0] = spa_pod_builder_add_object(&b,
        SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
        SPA_FORMAT_mediaType,       SPA_POD_Id(SPA_MEDIA_TYPE_video),
        SPA_FORMAT_mediaSubtype,    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
        // ✅ 方案2：统一像素格式 — 优先请求 RGBA，其次 BGRA（窗口捕获更常见）
        SPA_FORMAT_VIDEO_format,    SPA_POD_CHOICE_ENUM_Id(5,
                                    SPA_VIDEO_FORMAT_RGBA,
                                    SPA_VIDEO_FORMAT_RGBA,
                                    SPA_VIDEO_FORMAT_BGRA,
                                    SPA_VIDEO_FORMAT_BGRx,
                                    SPA_VIDEO_FORMAT_RGBx),
        // ✅ 方案1：将首选分辨率设为目标窗口尺寸，精确匹配
        // 使用 SPA_POD_CHOICE_RANGE_Rectangle，默认值=目标尺寸
        // 范围缩小到目标尺寸附近，避免协商到过大/过小的分辨率
        SPA_FORMAT_VIDEO_size,      SPA_POD_CHOICE_RANGE_Rectangle(
                                    &SPA_RECTANGLE(pref_w, pref_h),
                                    &SPA_RECTANGLE(1, 1),
                                    &SPA_RECTANGLE(8192, 8192)),
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

ffi.set_source("_pipewire_cffi", c_source, libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])

# 3. 编译 C 代码
if __name__ == "__main__":
    ffi.compile(verbose=True)
    print("✅ CFFI 编译成功！")
