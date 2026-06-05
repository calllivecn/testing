    typedef void (*py_state_cb)(void* userdata, int old_state, int new_state);
    typedef void (*py_format_cb)(void* userdata, uint32_t w, uint32_t h, uint32_t fmt);
    typedef void (*py_frame_cb)(void* userdata, void* data, uint32_t size, uint32_t w, uint32_t h, uint32_t stride);

    void* create_recorder();
    void destroy_recorder(void* ctx);
    
    void set_callbacks(void* ctx, void* userdata, py_state_cb on_state, py_format_cb on_format, py_frame_cb on_frame);
    
    int connect_stream(void* ctx, uint32_t node_id);
    void run_loop(void* ctx);
    void stop_loop(void* ctx);
