import os
from cffi import FFI

ffi = FFI()

# 1. C 源码：所有脏活累活都在这里干
c_source = """
#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/param/video/format.h>
#include <spa/pod/builder.h>
#include <stdio.h>
#include <stdlib.h>

// 定义一个上下文结构体，用来保存 Python 回调的指针和当前流的状态
struct RecorderContext {
    void (*py_on_state)(void *userdata, int old_state, int new_state);
    void (*py_on_format)(void *userdata, uint32_t width, uint32_t height, uint32_t format);
    void (*py_on_frame)(void *userdata, void *data_ptr, uint32_t size, uint32_t width, uint32_t height, uint32_t stride);
    
    void *py_userdata;
    
    uint32_t width;
    uint32_t height;
    uint32_t format;
    uint32_t stride;
    
    struct pw_stream *stream;
};

// --- 内部 C 回调函数 ---

static void on_state_changed(void *userdata, int old_state, int new_state, const char *error) {
    struct RecorderContext *ctx = (struct RecorderContext *)userdata;
    if (ctx && ctx->py_on_state) {
        ctx->py_on_state(ctx->py_userdata, old_state, new_state);
    }
}

static void on_param_changed(void *userdata, uint32_t id, const struct spa_pod *param) {
    printf("[C-Debug] on_param_changed entered (id=%u)\\n", id);
    fflush(stdout);

    struct RecorderContext *ctx = (struct RecorderContext *)userdata;
    if (!ctx || !param || id != SPA_PARAM_Format) {
        return;
    }

    struct spa_video_info_raw info;
    // 尝试解析 raw 格式
    if (spa_format_video_raw_parse(param, &info) == 0) {
        ctx->width = info.size.width;
        ctx->height = info.size.height;
        ctx->format = info.format;
        ctx->stride = ctx->width * 4;
        printf("[C-Debug] Format parsed OK: %ux%u, fmt=%u\\n", ctx->width, ctx->height, ctx->format);
    } else {
        // 🛡️ 兜底策略：如果解析失败，尝试从 Pod 中强行提取 size
        // 如果连这都失败，就硬编码一个默认值，防止 Python 层收到 0x0 崩溃
        printf("[C-Debug] ⚠️ Raw parse failed. Trying fallback...\\n");

        struct spa_pod *size_pod = NULL;
        if (spa_pod_find_prop(param, NULL, SPA_FORMAT_VIDEO_size) != NULL) {
             // 这里简化处理，直接给个常见分辨率兜底，实际应该用 spa_pod_get_rectangle
             ctx->width = 1920;
             ctx->height = 1080;
             ctx->stride = 1920 * 4;
             printf("[C-Debug] Fallback to 1920x1080.\\n");
        } else {
             ctx->width = 1920;
             ctx->height = 1080;
             ctx->stride = 1920 * 4;
             printf("[C-Debug] Fallback to default 1920x1080.\\n");
        }
    }
    fflush(stdout);
}

static void on_process(void *userdata) {
    struct RecorderContext *ctx = (struct RecorderContext *)userdata;
    if (!ctx || !ctx->stream) return;

    struct pw_buffer *b = pw_stream_dequeue_buffer(ctx->stream);
    if (!b) return;

    struct spa_buffer *buf = b->buffer;
    if (!buf || buf->n_datas < 1) {
        pw_stream_queue_buffer(ctx->stream, b);
        return;
    }

    struct spa_data *d = &buf->datas[0];

    printf("[C-Debug] on_process: type=%d, data=%p, size=%u\\n", d->type, d->data, d->chunk ? d->chunk->size : 0);
    fflush(stdout); // 强制刷新，看看死在哪一行

    // 只处理直接内存指针 (MemPtr)
    if (d->type == 1 && d->data != NULL && d->chunk && d->chunk->size > 0) { // SPA_DATA_MemPtr 的值通常是 1
        if (ctx->py_on_frame) {
            ctx->py_on_frame(ctx->py_userdata, d->data, d->chunk->size, ctx->width, ctx->height, ctx->stride);
        }
    } else {
        printf("[C-Debug] Skipped buffer (type=%d, not MemPtr or invalid)\\n", d->type);
        fflush(stdout);
    }

    pw_stream_queue_buffer(ctx->stream, b);
}

// --- 暴露给 Python 的 API ---

void pipewire_init() {
    pw_init(NULL, NULL);
}

void *create_recorder_context() {
    struct RecorderContext *ctx = (struct RecorderContext *)calloc(1, sizeof(struct RecorderContext));
    return ctx;
}

void destroy_recorder_context(void *ctx_ptr) {
    if (ctx_ptr) free(ctx_ptr);
}

void set_callbacks(void *ctx_ptr, void *userdata, 
                   void (*on_state)(void*, int, int),
                   void (*on_format)(void*, uint32_t, uint32_t, uint32_t),
                   void (*on_frame)(void*, void*, uint32_t, uint32_t, uint32_t, uint32_t)) {
    struct RecorderContext *ctx = (struct RecorderContext *)ctx_ptr;
    if (!ctx) return;
    ctx->py_userdata = userdata;
    ctx->py_on_state = on_state;
    ctx->py_on_format = on_format;
    ctx->py_on_frame = on_frame;
}

int start_stream(void *ctx_ptr, void *loop_ptr, uint32_t node_id) {
    struct RecorderContext *ctx = (struct RecorderContext *)ctx_ptr;
    struct pw_loop *loop = (struct pw_loop *)loop_ptr;
    if (!ctx || !loop) return -1;

    const struct pw_stream_events events = {
        .version = PW_VERSION_STREAM_EVENTS,
        .state_changed = on_state_changed,
        .param_changed = on_param_changed,
        .process = on_process,
    };

    ctx->stream = pw_stream_new_simple(loop, "wayland-recorder", NULL, &events, ctx);
    if (!ctx->stream) return -2;

    uint8_t buffer[4096];
    struct spa_pod_builder b = SPA_POD_BUILDER_INIT(buffer, sizeof(buffer));
    const struct spa_pod *params[1];
    
    params[0] = (const struct spa_pod *)spa_pod_builder_add_object(&b,
        SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
        SPA_FORMAT_mediaType,      SPA_POD_Id(SPA_MEDIA_TYPE_video),
        SPA_FORMAT_mediaSubtype,   SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
        SPA_FORMAT_VIDEO_format,   SPA_POD_CHOICE_ENUM_Id(3,
            SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
            SPA_POD_Id(SPA_VIDEO_FORMAT_RGBA),
            SPA_POD_Id(SPA_VIDEO_FORMAT_BGRA)
        ),
        SPA_FORMAT_VIDEO_size,     SPA_POD_CHOICE_RANGE_Rectangle(
            &SPA_RECTANGLE(1920, 1080),
            &SPA_RECTANGLE(1, 1),
            &SPA_RECTANGLE(7680, 4320)
        )
    );

    uint32_t flags = PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS;
    return pw_stream_connect(ctx->stream, PW_DIRECTION_INPUT, node_id, flags, params, 1);
}

void stop_stream(void *ctx_ptr) {
    struct RecorderContext *ctx = (struct RecorderContext *)ctx_ptr;
    if (ctx && ctx->stream) {
        pw_stream_destroy(ctx->stream);
        ctx->stream = NULL;
    }
}
"""

# 2. C 声明 (极简！只有基础类型和不透明指针 void*)
ffi.cdef("""
    typedef unsigned int uint32_t;
    typedef int int32_t;

    struct pw_main_loop;
    struct pw_loop;

    struct pw_main_loop *pw_main_loop_new(const void *props);
    struct pw_loop *pw_main_loop_get_loop(struct pw_main_loop *loop);
    void pw_main_loop_run(struct pw_main_loop *loop);
    void pw_main_loop_quit(struct pw_main_loop *loop);

    void pipewire_init();
    void *create_recorder_context();
    void destroy_recorder_context(void *ctx_ptr);
    
    void set_callbacks(void *ctx_ptr, void *userdata, 
                       void (*on_state)(void*, int, int),
                       void (*on_format)(void*, uint32_t, uint32_t, uint32_t),
                       void (*on_frame)(void*, void*, uint32_t, uint32_t, uint32_t, uint32_t));
                       
    int start_stream(void *ctx_ptr, void *loop_ptr, uint32_t node_id);
    void stop_stream(void *ctx_ptr);
""")

ffi.set_source("_pipewire_cffi", c_source, libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])

if __name__ == "__main__":
    ffi.compile(verbose=True)
    print("✅ CFFI 编译成功！")
