#!/usr/bin/env python

import sys
import time
import os

def monitor_net_io_without_lib(pid):
    """
    不使用第三方库，直接通过 /proc 文件系统监控指定 PID 的网络流量。
    """
    proc_net_path = f"/proc/{pid}/net/dev"

    if not os.path.exists(proc_net_path):
        print(f"错误: PID {pid} 不存在，或无法访问 {proc_net_path}。")
        return

    print(f"正在监控 PID {pid} 的网络流量... 按 Ctrl+C 退出。")
    print("-" * 50)
    print(f"{'Interface':<15} {'Rx (Bytes/s)':<20} {'Tx (Bytes/s)':<20}")
    print("-" * 50)

    # 读取初始网络统计数据
    def read_net_stats():
        """从 /proc/<pid>/net/dev 读取并解析数据"""
        stats = {}
        with open(proc_net_path, 'r') as f:
            lines = f.readlines()[2:]  # 跳过前两行表头
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 10:
                    iface = parts[0].strip(':')
                    stats[iface] = {
                        'rx_bytes': int(parts[1]),
                        'tx_bytes': int(parts[9])
                    }
        return stats

    # 获取初始统计数据
    try:
        initial_stats = read_net_stats()
    except (IOError, ValueError) as e:
        print(f"错误: 无法读取或解析 {proc_net_path}。可能是权限问题。")
        return

    while True:
        try:
            time.sleep(1)  # 每秒采样一次

            # 获取当前统计数据
            current_stats = read_net_stats()

            # 遍历所有网络接口
            for iface, initial_data in initial_stats.items():
                iface_current_data = current_stats.get(iface)

                if iface_current_data:
                    # 计算接收和发送的字节增量
                    rx_delta = iface_current_data['rx_bytes'] - initial_data['rx_bytes']
                    tx_delta = iface_current_data['tx_bytes'] - initial_data['tx_bytes']
                    
                    # 只有当有流量变化时才打印
                    if rx_delta > 0 or tx_delta > 0:
                        print(f"{iface:<15} {rx_delta:<20.2f} {tx_delta:<20.2f}")
            
            # 更新初始统计数据，为下一次循环做准备
            initial_stats = current_stats

        except (IOError, ValueError):
            print("\n进程已退出或无法访问文件。")
            break
        except KeyboardInterrupt:
            print("\n监控已停止。")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 monitor_net.py <PID>")
        sys.exit(1)
    
    try:
        pid = int(sys.argv[1])
        monitor_net_io_without_lib(pid)
    except ValueError:
        print("错误: PID 必须是数字。")
        sys.exit(1)
