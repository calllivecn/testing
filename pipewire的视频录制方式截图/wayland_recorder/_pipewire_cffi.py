
from cffi import FFI

ffi = FFI()

# 1. C 接口定义 (严格对齐真实头文件)
ffi.cdef("""
    // 不透明结构体声明
    struct pw_main_loop;
    struct pw_loop;
    struct pw_stream;
    struct spa_pod;
    struct pw_stream_control; 
    
    // 严格对齐真实的 struct spa_data 
    struct spa_chunk { uint32_t offset; uint32_t size; uint32_t stride; uint32_t flags; };
    struct spa_data { 
        uint32_t type; 
        uint32_t flags; 
        int64_t fd;          
        uint32_t mapoffset; 
        uint32_t maxsize; 
        void *data; 
        struct spa_chunk *chunk; // 这是一个指针
    };
    struct spa_meta { uint32_t type; uint32_t size; void *data; };
    struct spa_buffer { uint32_t n_metas; uint32_t n_datas; struct spa_meta *metas; struct spa_data *datas; };
    struct pw_buffer { struct spa_buffer *buffer; void *user_data; uint64_t size; uint64_t requested; };
    
    // 回调函数类型
    typedef void (*pw_stream_event_process_t)(void *data);
    typedef void (*pw_stream_event_state_changed_t)(void *data, int old_state, int state, const char *error);
    
    struct pw_stream_events {
        uint32_t version; 
        void (*destroy)(void *data); 
        pw_stream_event_state_changed_t state_changed;
        void (*control_info)(void *data, uint32_t id, const struct pw_stream_control *control); 
        void (*io_changed)(void *data, uint32_t id, void *area, uint32_t size);
        void (*param_changed)(void *data, uint32_t id, const struct spa_pod *param); 
        void (*add_buffer)(void *data, struct pw_buffer *buffer);
        void (*remove_buffer)(void *data, struct pw_buffer *buffer); 
        pw_stream_event_process_t process; 
        void (*trigger_done)(void *data);
    };

    // PipeWire 核心 API
    void pw_init(int *argc, char **argv[]);
    struct pw_main_loop *pw_main_loop_new(const void *props);
    struct pw_loop *pw_main_loop_get_loop(struct pw_main_loop *loop);
    int pw_main_loop_run(struct pw_main_loop *loop);
    int pw_main_loop_quit(struct pw_main_loop *loop);
    
    struct pw_stream *pw_stream_new_simple(struct pw_loop *loop, const char *name, void *props, const struct pw_stream_events *events, void *data);
    
    // 第 5 个参数改为 const struct spa_pod **
    int pw_stream_connect(struct pw_stream *stream, uint32_t direction, uint32_t target_id, uint32_t flags, const struct spa_pod **params, uint32_t n_params);
    
    struct pw_buffer *pw_stream_dequeue_buffer(struct pw_stream *stream);
    int pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buf);
    void pw_stream_destroy(struct pw_stream *stream);

    // SPA POD Builder
    struct spa_pod_builder { void *data; uint32_t size; uint32_t _padding; };
    void spa_pod_builder_init(struct spa_pod_builder *builder, void *data, uint32_t size);
    
    // 自定义 C 包装函数
    const struct spa_pod *build_format_pod(struct spa_pod_builder *builder, uint32_t format_id);
""")

# 2. 真实的 C 代码实现
ffi.set_source("_pipewire_cffi", """
    #include <pipewire/pipewire.h>
    #include <spa/param/video/format-utils.h>
    #include <spa/param/video/format.h>

    const struct spa_pod *build_format_pod(struct spa_pod_builder *builder, uint32_t format_id) {
        // 🎯 核心修复：放弃复杂的 CHOICE 宏，直接使用最稳定的基础 POD 构建方式
        // 告诉 PipeWire：我只要这个 format_id (BGRx)，并且我不限制分辨率和帧率，你按屏幕原生的给我就行。
        return (const struct spa_pod *)spa_pod_builder_add_object(builder,
            SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
            SPA_FORMAT_mediaType,      SPA_POD_Id(SPA_MEDIA_TYPE_video),
            SPA_FORMAT_mediaSubtype,   SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
            SPA_FORMAT_VIDEO_format,   SPA_POD_Id(format_id));
    }
""", libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])

if __name__ == "__main__":
    print("🔨 正在编译 PipeWire CFFI 扩展...")
    ffi.compile(verbose=True)
    print("✅ 编译成功！生成了 _pipewire_cffi 模块")
