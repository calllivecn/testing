
import hashlib
import timeit
import os
import platform

# 准备数据：生成一个 50MB 的随机二进制数据块
# 模拟大文件处理场景
DATA_SIZE = 50 * 1024 * 1024
payload = os.urandom(DATA_SIZE)

print(f"正在基准测试 (Python {platform.python_version()}, Platform: {platform.machine()})...")
print(f"数据大小: {DATA_SIZE / 1024 / 1024:.2f} MB")
print("-" * 40)

def benchmark_algo(algo_name):
    # 获取哈希对象
    h = hashlib.new(algo_name)
    # 更新数据
    h.update(payload)
    # 获取摘要（触发最终计算）
    return h.digest()

# 定义我们要测试的算法列表
algos = ['sha256', 'sha512', 'sha3_256', 'sha3_512']

for algo in algos:
    # 检查算法是否在当前环境可用
    if algo not in hashlib.algorithms_available:
        print(f"{algo}: 不支持")
        continue

    # 运行 5 次取平均值，减少波动
    # number=1 表示每次 setup 运行 1 次函数
    timer = timeit.Timer(lambda: benchmark_algo(algo))
    try:
        # 运行 5 次测试
        times = timer.repeat(repeat=5, number=1)
        avg_time = sum(times) / len(times)
        throughput = (DATA_SIZE / 1024 / 1024) / avg_time
        
        print(f"{algo:<10} : {avg_time:.4f} 秒 | 吞吐量: {throughput:.2f} MB/s")
    except Exception as e:
        print(f"{algo:<10} : 出错 ({e})")

print("-" * 40)
print("注意观察: 如果 CPU 支持 SHA 扩展指令集，sha256 可能会异常得快。")
print("否则，sha512 通常会胜出。SHA-3 通常是最慢的。")
