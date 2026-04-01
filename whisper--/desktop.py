import tkinter as tk
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import io
import threading
import time

import httpx  # 新增


# ==========================================
# 1. 模拟你的 whisper 函数
# ==========================================
def whisper_test(audio: bytes) -> str:
    """
    接收 WAV 格式的音频字节流，返回识别文本。
    这里使用 time.sleep 模拟 AI 识别的耗时过程。
    """
    print(f"[后台] 收到音频数据，大小：{len(audio)} 字节，开始识别...")
    time.sleep(1.5)
    result = "这是 Whisper 识别出来的测试文本！(PipeWire 录音很棒)"
    print(f"[后台] whisper 返回：{result}")  # 新增调试
    return result


# ==========================================
# 1. 配置 Whisper API 服务地址
# ==========================================
WHISPER_API_URL = "http://10.1.3.1:9000/asr"  # 根据你的服务地址修改

# ==========================================
# 2. 重写 whisper 函数 - 调用远程 API
# ==========================================
def whisper(audio: bytes) -> str:
    """
    接收 WAV 格式的音频字节流，调用远程 Whisper API 返回识别文本。
    
    参数:
        audio: WAV 格式的音频字节数据
    
    返回:
        识别出的文本字符串
    """
    print(f"[后台] 收到音频数据，大小：{len(audio)} 字节，开始调用 API...")
    
    try:
        # 使用 httpx 发送 multipart/form-data 请求
        with httpx.Client(timeout=60.0) as client:
            files = {
                "audio_file": ("audio.wav", audio, "audio/wav")
            }
            data = {
                "encode": "true",        # 让服务端用 ffmpeg 编码
                "task": "transcribe",    # 转录任务
                "language": "zh",        # 指定中文 (可选，不指定则自动检测)
                "output": "txt"          # 返回纯文本
            }
            
            response = client.post(WHISPER_API_URL, files=files, data=data)
            response.raise_for_status()  # 检查 HTTP 错误
            
            # 解析返回的 JSON (根据文档返回的是字符串)
            result = response.json()
            
            print(f"[后台] API 返回：{result}")
            return result
            
    except httpx.TimeoutException:
        print("[后台] 错误：API 请求超时")
        return "❌ 识别超时，请重试"
    except httpx.ConnectError:
        print("[后台] 错误：无法连接到 Whisper 服务")
        return "❌ 无法连接到服务，请检查服务是否运行"
    except Exception as e:
        print(f"[后台] 错误：{str(e)}")
        return f"❌ 识别失败：{str(e)}"


# ==========================================
# 2. Tkinter 录音界面主程序
# ==========================================
class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PipeWire 快捷录音助手")
        self.root.geometry("800x600")
        
        # --- 音频相关参数 ---
        self.samplerate = 16000
        self.channels = 1
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self.result_queue = queue.Queue()  # 新增：线程安全的结果队列
        self.processing = False  # 新增：防止重复处理
        
        # --- 界面组件 ---
        self.status_label = tk.Label(root, text="🟢 准备就绪", font=("Arial", 14), fg="green")
        self.status_label.pack(pady=10)
        
        self.instructions = tk.Label(root, text="【快捷键】\n按下 [空格键] : 开始/停止录音\n按下 [Esc 键] : 取消当前录音", justify="center")
        self.instructions.pack(pady=10)
        
        self.text_box = tk.Text(root, height=8, width=45, font=("Arial", 12))
        self.text_box.pack(pady=10)
        
        # --- 绑定快捷键 ---
        self.root.bind("<space>", self.toggle_recording)
        self.root.bind("<Escape>", self.cancel_recording)
        
        # 新增：启动主线程轮询
        self.root.after(100, self.check_results)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, flush=True)
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def toggle_recording(self, event=None):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if self.is_recording or self.processing:
            return
            
        self.is_recording = True
        self.audio_queue.queue.clear()
        self.status_label.config(text="🔴 录音中... (再按空格结束)", fg="red")
        self.text_box.delete("1.0", tk.END)
        
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.processing = True  # 标记正在处理
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
        self.status_label.config(text="⏳ 正在处理和识别...", fg="orange")
        
        threading.Thread(target=self.process_audio, daemon=True).start()

    def cancel_recording(self, event=None):
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
        self.audio_queue.queue.clear()
        self.processing = False
        self.status_label.config(text="❌ 录音已取消", fg="grey")

    def process_audio(self):
        """后台线程处理音频"""
        try:
            print("[process_audio] 开始处理")  # 调试
            audio_data = []
            while True:
                try:
                    chunk = self.audio_queue.get_nowait()
                    audio_data.append(chunk)
                except queue.Empty:
                    break
            
            print(f"[process_audio] 收到 {len(audio_data)} 个音频块")  # 调试
            
            if len(audio_data) == 0:
                self.result_queue.put(("status", "⚠️ 录音太短，无数据", "orange"))
                self.processing = False
                return

            full_audio = np.concatenate(audio_data, axis=0)
            print(f"[process_audio] 拼接后形状：{full_audio.shape}")  # 调试

            virtual_file = io.BytesIO()
            sf.write(virtual_file, full_audio, self.samplerate, format='WAV', subtype='PCM_16')
            audio_bytes = virtual_file.getvalue()
            print(f"[process_audio] WAV 大小：{len(audio_bytes)}")  # 调试

            result_text = whisper(audio_bytes)
            print(f"[process_audio] 准备发送结果到队列")  # 调试
            
            # 关键修复：把结果放入队列，而不是直接调用 root.after()
            self.result_queue.put(("result", result_text, None))
            
        except Exception as e:
            import traceback
            print(f"[process_audio] 错误：{traceback.format_exc()}")
            self.result_queue.put(("status", f"❌ 出错：{str(e)}", "red"))
        finally:
            self.processing = False

    def check_results(self):
        """主线程定期检查结果队列"""
        try:
            while True:
                msg_type, text, color = self.result_queue.get_nowait()
                print(f"[check_results] 收到消息：{msg_type}")  # 调试
                if msg_type == "result":
                    self.show_result(text)
                elif msg_type == "status":
                    self.status_label.config(text=text, fg=color)
        except queue.Empty:
            pass
        
        # 继续轮询
        self.root.after(100, self.check_results)

    def show_result(self, text):
        print(f"[show_result] 显示：{text}")  # 调试
        self.status_label.config(text="✅ 识别完成", fg="green")
        self.text_box.insert(tk.END, text + "\n")
        self.text_box.see(tk.END)

# ==========================================
# 3. 启动程序
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.lift()
    root.attributes('-topmost', True)
    root.attributes('-topmost', False)
    root.focus_force()
    
    root.mainloop()