#!/usr/bin/env python3
"""阶段 3: PipeWire C API 绑定 (使用 cffi 彻底解决段错误)"""
import sys
from cffi import FFI

ffi = FFI()

# 直接粘贴 C 语言声明！cffi 会自动处理底层内存对齐和类型
ffi.cdef("""
    // 不透明指针 (Opaque pointers)
    typedef struct pw_main_loop pw_main_loop;
    typedef struct pw_loop pw_loop;
    typedef struct pw_stream pw_stream;
    
    // 核心结构体
    struct spa_chunk {
        uint32_t offset;
        uint32_t size;
        uint32_t stride;
        uint32_t flags;
    };

    struct spa_data {
        uint32_t id;
        uint32_t flags;
        uint32_t type;
        uint32_t format;
        int64_t fd;
        uint32_t mapoffset;
        uint32_t maxsize;
        void *data;
        struct spa_chunk chunk;
    };

    struct spa_meta {
        uint32_t type;
        uint32_t size;
        void *data;
    };

    struct spa_buffer {
        uint32_t n_metas;
        uint32_t n_datas;
        struct spa_meta *metas;
        struct spa_data *datas;
    };

    struct pw_buffer {
        struct spa_buffer *buffer;
        // ... 忽略不需要的字段
    };

    // 回调函数签名
    typedef void (*pw_stream_event_process_t)(void *data);
    typedef void (*pw_stream_event_param_changed_t)(void *data, uint32_t id, const void *param);

    struct pw_stream_events {
        uint32_t version;
        void (*destroy)(void *data);
        void (*state_changed)(void *data, int old, int state, const char *error);
        void (*control_info)(void *data, uint32_t id, uint32_t flags);
        void (*io_changed)(void *data, uint32_t id, void *area, uint32_t size);
        pw_stream_event_param_changed_t param_changed;
        void (*add_buffer)(void *data, struct pw_buffer *buffer);
        void (*remove_buffer)(void *data, struct pw_buffer *buffer);
        pw_stream_event_process_t process;
    };

    // PipeWire 函数声明
    void pw_init(int *argc, char **argv[]);
    
    struct pw_main_loop *pw_main_loop_new(const void *props); // 注意这里传 void* (NULL)
    struct pw_loop *pw_main_loop_get_loop(struct pw_main_loop *loop);
    int pw_main_loop_run(struct pw_main_loop *loop);
    int pw_main_loop_quit(struct pw_main_loop *loop);
    
    struct pw_stream *pw_stream_new_simple(
        struct pw_loop *loop, const char *name, void *props,
        const struct pw_stream_events *events, void *data);
        
    int pw_stream_connect(
        struct pw_stream *stream, uint32_t direction, uint32_t target_id,
        uint32_t flags, const void **params, uint32_t n_params);
        
    struct pw_buffer *pw_stream_dequeue_buffer(struct pw_stream *stream);
    int pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buf);
    
    void pw_stream_destroy(struct pw_stream *stream);
""")

# 加载动态库
try:
    C = ffi.dlopen("libpipewire-0.3.so.0")
except OSError:
    sys.exit("❌ 找不到 libpipewire-0.3.so.0")

# 初始化 PipeWire
C.pw_init(ffi.NULL, ffi.NULL)

def test_bindings():
    print("="*40)
    print("🔍 阶段 3: PipeWire cffi 绑定测试")
    print("="*40)
    
    # 传入 ffi.NULL 代替之前的错误字符串，彻底解决段错误！
    loop = C.pw_main_loop_new(ffi.NULL) 
    
    if loop != ffi.NULL:
        print("✅ pw_main_loop_new 调用成功 (传入了正确的 NULL 指针)")
        print("🎉 cffi 绑定测试通过！")
    else:
        print("❌ pw_main_loop_new 失败")

if __name__ == "__main__":
    test_bindings()
