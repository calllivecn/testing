from cffi import FFI

ffi = FFI()

# ==============================================================================
# 1. C 接口定义 (cdef) - 严格对齐 PipeWire 0.3 真实头文件
# ==============================================================================
ffi.cdef("""
    // --- 不透明结构体声明 (避免在 Python 端猜测大小) ---
    struct pw_main_loop;
    struct pw_loop;
    struct pw_stream;
    struct spa_pod;
    struct spa_pod_builder; 
    struct pw_stream_control; 
    struct spa_command; // ✅ 修复：新增 spa_command 声明
    
    // --- 严格对齐真实的 struct spa_data ---
    struct spa_chunk { 
        uint32_t offset; 
        uint32_t size; 
        uint32_t stride; 
        uint32_t flags; 
    };
    
    struct spa_data { 
        uint32_t type; 
        uint32_t flags; 
        int64_t fd;          
        uint32_t mapoffset; 
        uint32_t maxsize; 
        void *data; 
        struct spa_chunk *chunk; 
    };
    
    struct spa_meta { uint32_t type; uint32_t size; void *data; };
    struct spa_buffer { uint32_t n_metas; uint32_t n_datas; struct spa_meta *metas; struct spa_data *datas; };
    struct pw_buffer { struct spa_buffer *buffer; void *user_data; uint64_t size; uint64_t requested; };
    
    // --- 回调函数类型 ---
    typedef void (*pw_stream_event_process_t)(void *data);
    typedef void (*pw_stream_event_state_changed_t)(void *data, int old_state, int state, const char *error);
    
    struct pw_stream_events {
        uint32_t version; 
        void (*destroy)(void *data); 
        void (*state_changed)(void *data, int old_state, int state, const char *error);
        void (*control_info)(void *data, uint32_t id, const struct pw_stream_control *control); 
        void (*io_changed)(void *data, uint32_t id, void *area, uint32_t size);
        void (*param_changed)(void *data, uint32_t id, const struct spa_pod *param); 
        void (*add_buffer)(void *data, struct pw_buffer *buffer);
        void (*remove_buffer)(void *data, struct pw_buffer *buffer); 
        void (*process)(void *data); 
        
        // 补齐 PipeWire 0.3.22+ 新增的字段
        void (*drained)(void *data);   
        // ✅ 修复：修正 command 回调的参数类型
        void (*command)(void *data, const struct spa_command *command); 
        
        void (*trigger_done)(void *data);
    };

    // --- PipeWire 核心 API ---
    void pw_init(int *argc, char **argv[]);
    struct pw_main_loop *pw_main_loop_new(const void *props);
    struct pw_loop *pw_main_loop_get_loop(struct pw_main_loop *loop);
    int pw_main_loop_run(struct pw_main_loop *loop);
    int pw_main_loop_quit(struct pw_main_loop *loop);
    
    struct pw_stream *pw_stream_new_simple(struct pw_loop *loop, const char *name, void *props, const struct pw_stream_events *events, void *data);
    
    int pw_stream_connect(struct pw_stream *stream, uint32_t direction, uint32_t target_id, uint32_t flags, const struct spa_pod **params, uint32_t n_params);
    
    struct pw_buffer *pw_stream_dequeue_buffer(struct pw_stream *stream);
    int pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buf);
    void pw_stream_destroy(struct pw_stream *stream);

    // --- 自定义 C 包装函数 ---
    const struct spa_pod *build_video_format_pod(
        uint32_t format_id, 
        uint32_t width, 
        uint32_t height, 
        uint32_t min_fps, 
        uint32_t max_fps
    );
    
    void free_format_pod(const struct spa_pod *pod);
""")

# ==============================================================================
# 2. 真实的 C 代码实现 (set_source)
# ==============================================================================
ffi.set_source("_pipewire_cffi", """
    #include <pipewire/pipewire.h>
    #include <spa/param/video/format-utils.h>
    #include <spa/param/video/format.h>
    #include <spa/pod/builder.h>
    #include <stdlib.h>
    #include <string.h>

    const struct spa_pod *build_video_format_pod(
        uint32_t format_id, 
        uint32_t width, 
        uint32_t height, 
        uint32_t min_fps, 
        uint32_t max_fps
    ) {
        uint8_t *buffer = (uint8_t *)calloc(1, 1024);
        if (!buffer) return NULL;

        struct spa_pod_builder *builder = (struct spa_pod_builder *)calloc(1, sizeof(struct spa_pod_builder));
        if (!builder) { free(buffer); return NULL; }

        spa_pod_builder_init(builder, buffer, 1024);

        // ✅ 修复：去掉未使用的 pod 变量，直接调用
        spa_pod_builder_add_object(builder,
            SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
            SPA_FORMAT_mediaType,      SPA_POD_Id(SPA_MEDIA_TYPE_video),
            SPA_FORMAT_mediaSubtype,   SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
            SPA_FORMAT_VIDEO_format,   SPA_POD_Id(format_id),
            SPA_FORMAT_VIDEO_size,     SPA_POD_CHOICE_RANGE_Rectangle(
                &SPA_RECTANGLE(width, height),    
                &SPA_RECTANGLE(1, 1),             
                &SPA_RECTANGLE(7680, 4320)        
            ),
            SPA_FORMAT_VIDEO_framerate, SPA_POD_CHOICE_RANGE_Fraction(
                &SPA_FRACTION(min_fps, 1),        
                &SPA_FRACTION(1, 1),              
                &SPA_FRACTION(max_fps, 1)         
            )
        );

        free(builder);
        return (const struct spa_pod *)buffer;
    }

    void free_format_pod(const struct spa_pod *pod) {
        if (pod) {
            free((void *)pod);
        }
    }
""", libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])

# ==============================================================================
# 3. 编译入口
# ==============================================================================
if __name__ == "__main__":
    print("🔨 正在编译 PipeWire CFFI 扩展 (全面修复版)...")
    try:
        ffi.compile(verbose=True)
        print("✅ 编译成功！生成了 _pipewire_cffi 模块")
    except Exception as e:
        print(f"❌ 编译失败: {e}")
        print("💡 提示：请确保已安装 pipewire 和 spa 的开发头文件")
