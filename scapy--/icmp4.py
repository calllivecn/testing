# 使用 scapy 构造一个简单的 ICMP 包 (Ping)
from scapy.all import IP, ICMP, sr1

def send_ping(target_ip):
    # 构造 IP 层（网络层）和 ICMP 层（传输/控制层）
    packet = IP(dst=target_ip) / ICMP()
    
    # 发送并等待响应 (sr1: send and receive one)
    print(f"正在向 {target_ip} 发送 ICMP 包...")
    reply = sr1(packet, timeout=2, verbose=False)
    
    if reply:
        # 这里的 reply.summary() 会展示各层的解析结果
        print(f"收到回复: {reply.summary()}")
    else:
        print("请求超时。")

#send_ping("8.8.8.8")
send_ping("192.168.1.1")
