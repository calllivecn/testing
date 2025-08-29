import argparse
import time
import psutil

# 定义单位
UNITS = ['B/s', 'KB/s', 'MB/s', 'GB/s']

def convert_bytes(bytes_value):
    """
    将字节值转换为更易读的单位 (B/s, KB/s, MB/s, GB/s)。
    """
    # 遍历单位，直到找到合适的单位
    for unit in UNITS:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} {UNITS[-1]}"

def get_net_io_counters(interface=None):
    """
    获取指定或所有非本地回环网络接口的输入/输出字节数。
    """
    net_io = psutil.net_io_counters(pernic=True)
    if interface:
        # 如果指定了接口，则只返回该接口的数据
        return net_io.get(interface, None)
    else:
        # 如果未指定，则汇总所有非本地回环接口的数据
        total_bytes_sent = 0
        total_bytes_recv = 0
        for iface, counters in net_io.items():
            # 排除本地回环接口 (lo)
            if iface != 'lo':
                total_bytes_sent += counters.bytes_sent
                total_bytes_recv += counters.bytes_recv
        return psutil._common.snetio(
            bytes_sent=total_bytes_sent,
            bytes_recv=total_bytes_recv,
            packets_sent=0,
            packets_recv=0,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0
        )

def monitor_speed(interval=1, interface=None, monitor_upload=True, monitor_download=True):
    """
    监控并显示网络速度。
    """
    # 检查指定的接口是否存在
    if interface and interface not in psutil.net_io_counters(pernic=True):
        print(f"错误: 找不到网络接口 '{interface}'。")
        print("可用接口有:", ', '.join(psutil.net_io_counters(pernic=True).keys()))
        return

    print("--- 网络速度监控 ---")
    if interface:
        print(f"正在监控接口: {interface}")
    else:
        print("正在监控所有非本地回环接口")
    print(f"检测间隔: {interval} 秒")
    print("-" * 20)
    
    # 获取初始字节数
    initial_io = get_net_io_counters(interface)
    if not initial_io:
        print(f"错误: 无法获取接口 '{interface}' 的数据。")
        return

    try:
        while True:
            time.sleep(interval)
            
            # 获取当前字节数
            current_io = get_net_io_counters(interface)
            if not current_io:
                print(f"错误: 无法获取接口 '{interface}' 的数据。")
                break

            # 计算速度
            # 使用 float() 确保除法结果为浮点数
            bytes_sent = float(current_io.bytes_sent - initial_io.bytes_sent)
            bytes_recv = float(current_io.bytes_recv - initial_io.bytes_recv)
            
            # 速度 = (新字节数 - 旧字节数) / 时间间隔
            upload_speed = bytes_sent / interval
            download_speed = bytes_recv / interval

            # 打印结果
            output = ""
            if monitor_download:
                output += f"下载: {convert_bytes(download_speed)}"
            if monitor_download and monitor_upload:
                output += " | "
            if monitor_upload:
                output += f"上传: {convert_bytes(upload_speed)}"

            print(output, end='\r') # 使用 \r 实现单行刷新
            
            # 更新初始字节数
            initial_io = current_io

    except KeyboardInterrupt:
        print("\n监控已停止。")
    except Exception as e:
        print(f"\n发生错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 psutil 监控网络速度。")
    parser.add_argument("-i", "--interface", help="指定要监控的网络接口 (e.g., eth0)")
    parser.add_argument("-d", "--download", action="store_true", help="仅监控下载速度")
    parser.add_argument("-u", "--upload", action="store_true", help="仅监控上传速度")
    parser.add_argument("-s", "--seconds", type=int, default=1, help="指定检测时间间隔 (秒)，默认为 1")
    
    args = parser.parse_args()
    
    # 如果同时指定了 -d 和 -u，则都监控。如果只指定了一个，则只监控那一个。
    if args.download or args.upload:
        monitor_upload = args.upload
        monitor_download = args.download
    else:
        monitor_upload = True
        monitor_download = True
        
    monitor_speed(args.seconds, args.interface, monitor_upload, monitor_download)
