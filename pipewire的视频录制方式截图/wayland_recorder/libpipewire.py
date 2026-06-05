import threading
import traceback
from _pipewire_cffi import ffi, lib as C

class PipeWireStream:
    def __init__(self, node_id):

        C.pipewire_init()

        self.node_id = node_id
        self._ctx = C.create_recorder_context()
        self._loop = C.pw_main_loop_new(ffi.NULL)
        self._thread = None
        self._running = False
        
        # Python 侧的回调
        self.on_state_changed = None
        self.on_format_changed = None
        self.on_frame = None
        
        # 防止 CFFI 回调被垃圾回收
        self._c_callbacks = []
        self._setup_callbacks()

    def _setup_callbacks(self):
        # ✅ 修复：onerror 函数必须接收 3 个参数 (exc_type, exc_value, exc_tb)
        def _handle_callback_error(exc_type, exc_value, exc_tb):
            print(f"[Py-Debug] ⚠️ 回调函数内部发生异常: {exc_value}")
            traceback.print_exception(exc_type, exc_value, exc_tb)

        @ffi.callback("void(void*, int, int)", onerror=_handle_callback_error)
        def _c_on_state(userdata, old, new):
            print(f"[Py-Debug] _c_on_state: {old} -> {new}")
            if self.on_state_changed:
                self.on_state_changed(old, new)

        @ffi.callback("void(void*, uint32_t, uint32_t, uint32_t)", onerror=_handle_callback_error)
        def _c_on_format(userdata, w, h, fmt):
            print(f"[Py-Debug] _c_on_format: {w}x{h}, fmt={fmt}")
            if self.on_format_changed:
                self.on_format_changed(w, h, fmt)

        @ffi.callback("void(void*, void*, uint32_t, uint32_t, uint32_t, uint32_t)", onerror=_handle_callback_error)
        def _c_on_frame(userdata, data_ptr, size, w, h, stride):
            if self.on_frame:
                frame_data = ffi.buffer(data_ptr, size)
                self.on_frame(frame_data, w, h, stride)

        self._c_callbacks.extend([_c_on_state, _c_on_format, _c_on_frame])
        C.set_callbacks(self._ctx, ffi.NULL, _c_on_state, _c_on_format, _c_on_frame)

    def _run_loop(self):
        try:
            loop_ptr = C.pw_main_loop_get_loop(self._loop)
            res = C.start_stream(self._ctx, loop_ptr, self.node_id)
            if res < 0:
                print(f"❌ PipeWire 启动失败: {res}")
                return
            C.pw_main_loop_run(self._loop)
        except Exception as e:
            print(f"❌ PipeWire 线程异常: {e}")
            traceback.print_exc()
        finally:
            print("🧹 [PipeWire] 线程已安全退出")

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running: return
        self._running = False
        C.pw_main_loop_quit(self._loop)
        C.stop_stream(self._ctx)
        if self._thread:
            self._thread.join(timeout=2.0)
        C.destroy_recorder_context(self._ctx)
    

    def set_target_fps(self, fps: int):
        C.set_target_fps(self._ctx, fps)

    def set_crop_region(self, enabled: bool, x: int, y: int, w: int, h: int):
        C.set_crop_region(self._ctx, enabled, x, y, w, h)

    def __del__(self):
        self.stop()

