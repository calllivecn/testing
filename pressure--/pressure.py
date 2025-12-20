#!/usr/bin/env python
"""
Linux PSI (Pressure Stall Information) 监控脚本

该脚本读取 /proc/pressure/cpu、memory、io 文件，解析 PSI 指标，
并提供 CLI 终端输出和 JSON 格式输出两种模式。

使用方法:
    # CLI 终端持续监控，每 2 秒更新一次
    python psi_monitor.py -T 2

    # 输出一次 JSON 格式数据，供其他工具调用
    python psi_monitor.py --json

    # 输出帮助
    python psi_monitor.py -h
"""

import argparse
import json
import time
import os
import sys
from io import StringIO


def read_psi_data():
    """
    读取 PSI 数据，返回一个字典结构
    """
    psi_data = {}
    resources = ['cpu', 'memory', 'io']

    for resource in resources:
        path = f'/proc/pressure/{resource}'
        if not os.path.exists(path):
            print(f"警告: {path} 不存在，可能内核未启用 PSI 支持。", file=sys.stderr)
            psi_data[resource] = None
            continue

        try:
            with open(path, 'r') as f:
                content = f.read().strip()
        except PermissionError:
            print(f"错误: 无法读取 {path}，权限不足。", file=sys.stderr)
            psi_data[resource] = None
            continue
        except Exception as e:
            print(f"错误: 读取 {path} 时发生异常: {e}", file=sys.stderr)
            psi_data[resource] = None
            continue

        lines = content.split('\n')
        data = {}

        for line in lines:
            parts = line.split()
            if len(parts) < 4:
                continue

            level = parts[0].rstrip(':')
            metrics = {}
            for p in parts[1:]:
                k, v = p.split('=')
                if k.startswith('avg'):
                    # 将 avg10=0.00 转换为 avg10: 0.00
                    metrics[k] = float(v)
                elif k == 'total':
                    # total 为整数（微秒）
                    metrics[k] = int(v)

            data[level] = metrics

        psi_data[resource] = data

    return psi_data


def format_cli_output(psi_data):
    """
    格式化 CLI 终端输出到 StringIO 并返回字符串
    """
    output_buffer = StringIO()

    print("=" * 80, file=output_buffer)
    print("Linux PSI (Pressure Stall Information) 监控数据", file=output_buffer)
    print("=" * 80, file=output_buffer)

    for resource, data in psi_data.items():
        if data is None:
            print(f"\n【{resource.upper()}】 - 无法读取数据", file=output_buffer)
            continue

        print(f"\n【{resource.upper()}】", file=output_buffer)
        print("-" * 80, file=output_buffer)

        for level, metrics in data.items():
            print(f"  {level.upper()}: ", end="", file=output_buffer)
            for key, value in metrics.items():
                if key == 'total':
                    print(f"{key}={value:,}us", end=" ", file=output_buffer)
                else:
                    print(f"{key}={value:.2f}%", end=" ", file=output_buffer)
            print(file=output_buffer)  # 换行

        # 解释指标含义
        if resource == 'cpu':
            print("\n    指标说明:", file=output_buffer)
            print("      - some: 至少有一个任务因 CPU 不足而等待的时间占比", file=output_buffer)
            print("      - full: 所有非 idle 任务都因 CPU 不足而等待的时间占比", file=output_buffer)
        elif resource == 'memory':
            print("\n    指标说明:", file=output_buffer)
            print("      - some: 至少有一个任务因内存不足而等待的时间占比", file=output_buffer)
            print("      - full: 所有非 idle 任务都因内存不足而等待的时间占比", file=output_buffer)
            print("              (full > 0 代表系统严重卡顿甚至无响应!)", file=output_buffer)
        elif resource == 'io':
            print("\n    指标说明:", file=output_buffer)
            print("      - some: 至少有一个任务因 I/O 不足而等待的时间占比", file=output_buffer)
            print("      - full: 所有非 idle 任务都因 I/O 不足而等待的时间占比", file=output_buffer)

    print("=" * 80, file=output_buffer)

    return output_buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(
        description="Linux PSI (Pressure Stall Information) 监控脚本",
        epilog="示例: python psi_monitor.py -T 2  # 每2秒刷新一次\n       python psi_monitor.py --json  # 输出JSON格式"
    )
    parser.add_argument('-T', '--time', type=float, default=None,
                        help='指定监控时间间隔（秒），如 -T 2。不指定则只输出一次 JSON。')
    parser.add_argument('--json', action='store_true',
                        help='输出 JSON 格式数据，供其他工具调用。')

    args = parser.parse_args()

    if args.json or args.time is None:
        data = read_psi_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if args.time <= 0:
        print("错误: -T 参数必须大于 0", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            data = read_psi_data()
            # 清屏并打印新数据
            os.system('clear' if os.name != 'nt' else 'cls')
            
            cli_output = format_cli_output(data)
            print(cli_output, end='')
            
            time.sleep(args.time)
    except KeyboardInterrupt:
        print("\n监控已停止。")
    except Exception as e:
        print(f"运行时发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()




