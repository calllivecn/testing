import tkinter as tk
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import io
import threading
import time

# ==========================================
# 1. 模拟你的 whisper 函数
# ==========================================
def whisper(audio: bytes) -> str:
    """
    接收 WAV 格式的音频字节流，返回识别文本。
    这里使用 time.sleep 模拟 AI 识别的耗时过程。
    """
    print(f"[后台] 收到音频数据，大小: {len(audio)} 字节，开始识别...")
    time.sleep(1.5) # 模拟网络请求或模型推理耗时
    return "这是 Whisper 识别出来的测试文本！(PipeWire 录音很棒)"

# ==========================================
# 2. Tkinter 录音界面主程序
# ==========================================
class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PipeWire 快捷录音助手")
        self.root.geometry("400x300")
        
        # --- 音频相关参数 ---
        self.samplerate = 16000
        self.channels = 1
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        
        # --- 界面组件 ---
        self.status_label = tk.Label(root, text="🟢 准备就绪", font=("Arial", 14), fg="green")
        self.status_label.pack(pady=10)
        
        self.instructions = tk.Label(root, text="【快捷键】\n按下 [空格键] : 开始/停止录音\n按下 [Esc 键] : 取消当前录音", justify="center")
        self.instructions.pack(pady=10)
        
        self.text_box = tk.Text(root, height=8, width=45, font=("Arial", 12))
        self.text_box.pack(pady=10)
        
        # --- 绑定快捷键 (窗口需要处于焦点状态) ---
        self.root.bind("<space>", self.toggle_recording)
        self.root.bind("<Escape>", self.cancel_recording)

    def audio_callback(self, indata, frames, time, status):
        """sounddevice 的底层回调：只要在录音，就会不断把音频块塞进这里"""
        if status:
            print(status, flush=True)
        if self.is_recording:
            # 将原始的 NumPy 数组拷贝并放入内存队列
            self.audio_queue.put(indata.copy())

    def toggle_recording(self, event=None):
        """空格键触发：切换录音/停止状态"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.audio_queue.queue.clear() # 清空旧数据
        self.status_label.config(text="🔴 录音中... (再按空格结束)", fg="red")
        self.text_box.delete("1.0", tk.END)
        
        # 启动非阻塞输入流
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        """停止录音并处理"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
        self.status_label.config(text="⏳ 正在处理和识别...", fg="orange")
        
        # 启动后台线程处理音频，防止界面卡死
        threading.Thread(target=self.process_audio, daemon=True).start()

    def cancel_recording(self, event=None):
        """Esc键触发：直接丢弃当前录音"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
        self.audio_queue.queue.clear() # 丢弃所有数据
        self.status_label.config(text="❌ 录音已取消", fg="grey")

    def process_audio(self):
        """在后台线程中从队列提取数据，转换为 WAV 字节流并调用 whisper"""
        # 1. 从队列中提取所有的录音片段并拼接成一个大数组
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        if len(audio_data) == 0:
            self.root.after(0, lambda: self.status_label.config(text="⚠️ 录音太短，无数据", fg="orange"))
            return

        # 将列表中的 numpy 数组纵向拼接
        full_audio = np.concatenate(audio_data, axis=0)

        # 2. 在内存中将 NumPy 数组转换为 WAV 格式的 bytes
        virtual_file = io.BytesIO()
        sf.write(virtual_file, full_audio, self.samplerate, format='WAV', subtype='PCM_16')
        audio_bytes = virtual_file.getvalue()

        # 3. 调用 whisper 函数 (执行 AI 识别)
        try:
            result_text = whisper(audio_bytes)
            # 使用 after 回到主线程更新 UI
            self.root.after(0, lambda: self.show_result(result_text))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"❌ 出错: {str(e)}", fg="red"))

    def show_result(self, text):
        """更新界面显示识别结果"""
        self.status_label.config(text="✅ 识别完成", fg="green")
        self.text_box.insert(tk.END, text + "\n")
        self.text_box.see(tk.END) # 滚动到底部

# ==========================================
# 3. 启动程序
# ==========================================
if __name__ == "__main__":
    # 在某些 Linux 环境下，可能需要手动指定设备
    # print(sd.query_devices())
    root = tk.Tk()
    app = AudioRecorderApp(root)
    
    # --- 窗口居中处理 ---
    root.update_idletasks()  # 更新任务以获取准确的窗口尺寸
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # --- 强制获取焦点 (确保快捷键立即生效) ---
    root.lift()                     # 将窗口层级提升
    root.attributes('-topmost', True) # 暂时置顶
    root.attributes('-topmost', False)# 取消置顶，但保留焦点
    root.focus_force()              # 强制输入焦点
    
    root.mainloop()