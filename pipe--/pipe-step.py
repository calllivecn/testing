import threading
import queue
import traceback
import sys
import time
from functools import wraps

class PipeStep:
    """
    支持链式调用、异常熔断、背压控制的 Python 多线程管道封装。
    """
    def __init__(self, func, name=None, maxsize=10):
        self.func = func
        self.name = name or func.__name__
        self.maxsize = maxsize  # 队列最大长度，用于控制背压
        
        self.in_q = None
        self.out_q = None
        self.thread = None
        
        # 全局停止信号 (Circuit Breaker)
        # 默认为 None，在链接(__or__)时会同步为同一个 Event 对象
        self.stop_event = None 

    def __or__(self, other):
        """
        实现 Shell 风格的管道链接: step1 | step2
        """
        if not isinstance(other, PipeStep):
            raise TypeError(f"管道下一级必须是 PipeStep 实例，而不是 {type(other)}")
        
        # 1. 创建连接队列
        bridge_q = queue.Queue(maxsize=self.maxsize)
        self.out_q = bridge_q
        other.in_q = bridge_q
        
        # 2. 同步停止信号 (Event)
        # 如果当前还没有 Event (链头)，则创建一个
        if self.stop_event is None:
            self.stop_event = threading.Event()
        
        # 将信号传递给下一级，确保整个链条共享同一个 Event
        other.stop_event = self.stop_event
        
        return other

    def _safe_put(self, item):
        """
        带熔断检查的安全写入。
        防止下游挂掉后，上游因为队列满而死锁在 put() 上。
        """
        while not self.stop_event.is_set():
            try:
                # 尝试写入，超时 0.1 秒以便检查 stop_event
                self.out_q.put(item, timeout=0.1)
                return True
            except queue.Full:
                continue # 队列满了，循环重试，顺便检查是否需要停止
        return False # 已收到停止信号，放弃写入

    def _worker(self):
        """线程工作主循环"""
        # 确保即使是独立的环节也有 Event
        if self.stop_event is None:
            self.stop_event = threading.Event()

        try:
            while not self.stop_event.is_set():
                # --- 1. 获取输入 ---
                data = None
                if self.in_q:
                    try:
                        # 带超时的 get，方便定期检查 stop_event
                        data = self.in_q.get(timeout=0.1)
                    except queue.Empty:
                        continue # 没数据，循环回去检查 stop_event
                    
                    if data is None:
                        break # 上游发送了 EOF (Poison Pill)

                # --- 2. 执行业务逻辑 ---
                # 注意：这里的 func 可能会抛出异常
                if self.in_q is None:
                    # 生成器模式 (Head)
                    results = self.func()
                else:
                    # 过滤器模式 (Pipe)
                    results = self.func(data)

                # --- 3. 发送输出 ---
                if results is not None:
                    # 归一化为列表处理
                    if not hasattr(results, '__iter__') or isinstance(results, (str, bytes)):
                        results = [results]
                    
                    for r in results:
                        # 如果 func 是生成器，我们需要遍历它
                        # 如果写入失败(比如收到停止信号)，直接跳出
                        if self.out_q:
                            if not self._safe_put(r):
                                break
        
        except Exception as e:
            # --- 异常熔断 ---
            print(f"\n[ERROR] 线程 '{self.name}' 崩溃: {e}", file=sys.stderr)
            traceback.print_exc()
            # 触发全局停止，通知所有兄弟线程
            self.stop_event.set()
            
        finally:
            # --- 清理现场 ---
            # 无论如何，向下游发送 EOF，防止下游卡死
            if self.out_q and not self.stop_event.is_set():
                try:
                    # 使用非阻塞 put，如果满了就算了(因为都在退出了)
                    self.out_q.put(None, block=False)
                except queue.Full:
                    pass
            
            # 可选：打印退出日志
            # print(f"[{self.name}] 线程退出")

    def start(self):
        self.thread = threading.Thread(target=self._worker, name=self.name, daemon=True)
        self.thread.start()
        return self

    def wait(self):
        if self.thread:
            self.thread.join()

# --- 装饰器语法糖 ---
def pipeable(func):
    return PipeStep(func)


# ==========================================
# 测试案例：模拟异常崩溃
# ==========================================

if __name__ == "__main__":
    print(">>> 启动管道测试：演示异常熔断机制")

    @pipeable
    def source():
        """产生数据"""
        for i in range(10):
            print(f"[Source] 产生: {i}")
            time.sleep(0.2)
            yield i
        print("[Source] 数据产生完毕")

    @pipeable
    def risky_process(num):
        """模拟处理，在特定数据上崩溃"""
        if num == 5:
            raise ValueError("遇到了炸弹数字 5，模拟崩溃！")
        return num * 2

    @pipeable
    def sink(num):
        """接收数据"""
        print(f"    [Sink] 接收到: {num}")
        time.sleep(0.5) # 模拟慢速消费，制造背压

    # 1. 组装管道
    # source (生产者) | risky_process (易崩处理) | sink (消费者)
    pipeline_head = source
    pipeline_mid = risky_process
    pipeline_tail = sink
    
    pipeline_head | pipeline_mid | pipeline_tail

    # 2. 启动
    # 只要启动了，它们就会在后台运行
    pipeline_tail.start()
    pipeline_mid.start()
    pipeline_head.start()

    # 3. 等待
    try:
        # 我们只需要等待最末端，或者全部等待
        # 由于有了 Event 机制，如果中间崩了，source 和 sink 都会感知并退出
        pipeline_head.wait()
        pipeline_mid.wait()
        pipeline_tail.wait()
    except KeyboardInterrupt:
        print("\n用户强制停止")
    
    print(">>> 主程序结束")
