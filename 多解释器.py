#!/usr/bin/python3
# py 3.14

import time
import os
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    InterpreterPoolExecutor  # Python 3.14+ 新特性
)

def cpu_intensive_task(n):
    """CPU 密集型任务：计算平方和（典型 GIL 受限场景）"""
    return sum(i * i for i in range(n))

def run_serial(n_tasks, task_size):
    """串行执行（基准测试）"""
    start = time.time()
    results = [cpu_intensive_task(task_size) for _ in range(n_tasks)]
    return time.time() - start, results

def run_thread_pool(n_tasks, task_size, max_workers):
    """线程池执行（受 GIL 限制）"""
    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(cpu_intensive_task, [task_size] * n_tasks))
    return time.time() - start, results

def run_process_pool(n_tasks, task_size, max_workers):
    """进程池执行（无 GIL 限制，但有 IPC 开销）"""
    start = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(cpu_intensive_task, [task_size] * n_tasks))
    return time.time() - start, results

def run_interpreter_pool(n_tasks, task_size, max_workers):
    """解释器池执行（Python 3.14+ 新特性）"""
    start = time.time()
    with InterpreterPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(cpu_intensive_task, [task_size] * n_tasks))
    return time.time() - start, results

if __name__ == "__main__":
    # 配置测试参数
    TASK_SIZE = 10**8  # 单任务计算量
    N_TASKS = 4        # 并行任务数（建议 = CPU 核心数）
    MAX_WORKERS = min(4, os.cpu_count() or 4)  # 避免过度并行
    
    print(f"测试环境: {os.cpu_count()} 核 CPU | 任务数={N_TASKS} | 单任务量={TASK_SIZE:_}\n")
    
    # 1. 串行执行（基准）
    serial_time, _ = run_serial(N_TASKS, TASK_SIZE)
    print(f"[串行] 单线程执行总耗时: {serial_time:.2f} 秒 (基准)")
    
    # 2. 线程池执行
    thread_time, _ = run_thread_pool(N_TASKS, TASK_SIZE, MAX_WORKERS)
    print(f"[线程池] ThreadPoolExecutor 耗时: {thread_time:.2f} 秒 "
          f"({serial_time/thread_time:.1f}x 加速 | GIL 限制明显)")
    
    # 3. 进程池执行
    process_time, _ = run_process_pool(N_TASKS, TASK_SIZE, MAX_WORKERS)
    print(f"[进程池] ProcessPoolExecutor 耗时: {process_time:.2f} 秒 "
          f"({serial_time/process_time:.1f}x 加速 | 启动开销大)")
    
    # 4. 解释器池执行 (Python 3.14+)
    try:
        interp_time, _ = run_interpreter_pool(N_TASKS, TASK_SIZE, MAX_WORKERS)
        print(f"[解释器池] InterpreterPoolExecutor 耗时: {interp_time:.2f} 秒 "
              f"({serial_time/interp_time:.1f}x 加速 | 无 GIL + 低 IPC 开销)")
        
        # 性能对比分析
        print("\n" + "="*50)
        print("性能对比分析 (耗时比例，以串行为 1.0):")
        print(f"线程池  : {thread_time/serial_time:.2f}x  (GIL 限制导致几乎无加速)")
        print(f"进程池  : {process_time/serial_time:.2f}x  (IPC 开销影响小规模任务)")
        print(f"解释器池: {interp_time/serial_time:.2f}x  (最佳平衡点)")
        print("="*50)
        
        # 关键结论
        if interp_time < process_time:
            print("\n✅ 解释器池优势场景:")
            print("- 任务规模中等（<100ms/任务），IPC 序列化开销显著时")
            print("- 需要环境隔离但避免进程创建开销（如插件系统）")
            print(f"- 实测加速比: 比进程池快 {(process_time/interp_time-1)*100:.0f}%")
        else:
            print("\n⚠️ 注意: 当任务量极大时，进程池可能反超（因解释器池有内存共享开销）")
    
    except NameError:
        print("\n[警告] 当前 Python 版本不支持 InterpreterPoolExecutor (需 3.14+)")
        print("请升级到 Python 3.14 或更高版本以测试此特性")
