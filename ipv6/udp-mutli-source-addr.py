
"""
处理listen, bind("::") 地址时+本地接口有多个ipv6地址时，server回复client的问题。

"""


import sys
import socket
import struct

HOST = '::'  # 服务器监听所有 IPv6 地址
PORT = 6789



def server_with_pktinfo():
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
        # 允许地址重用，以便快速重启服务器
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 开启 IP_PKTINFO 选项，用于获取接收到的数据包的目标地址信息
        # socket.IPPROTO_IPV6 是 IPv6 的协议级别
        # socket.IPV6_RECVPKTINFO 是对应的选项
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)

        s.bind((HOST, PORT))
        print(f"服务器已绑定到 [{HOST}]:{PORT} 并开启 IPV6_RECVPKTINFO")

        while True:
            # 使用 recvmsg() 来接收数据和控制消息
            # 1024 是数据缓冲区大小，64 是控制消息缓冲区大小
            data, ancdata, msg_flags, addr = s.recvmsg(1024, 64)

            client_addr, client_port = addr[0], addr[1]
            server_recv_addr = None # 存储数据包到达的服务器本地 IP 地址

            print(f"{ancdata=}")

            # 解析控制消息
            for cmsg_level, cmsg_type, cmsg_data in ancdata:
                if cmsg_level == socket.IPPROTO_IPV6 and cmsg_type == socket.IPV6_PKTINFO:
                    # cmsg_data 包含了 in6_pktinfo 结构体
                    # 格式: (ip6a_addr, ip6a_ifindex)
                    # ip6a_addr 是一个 16 字节的 IPv6 地址，ip6a_ifindex 是接口索引
                    server_recv_addr = socket.inet_ntop(socket.AF_INET6, cmsg_data[:16])
                    # if_index = struct.unpack("=I", cmsg_data[16:20])[0] # 如果需要接口索引

            if server_recv_addr:
                print(f"收到来自 [{client_addr}]:{client_port} 的数据到服务器本地地址 [{server_recv_addr}]:{PORT}")
                response = b"Hello from server!"

                # 构建控制消息，指定源 IP 地址 (server_recv_addr)
                # socket.inet_pton 将字符串 IPv6 地址转换为 16 字节的二进制
                pktinfo = socket.inet_pton(socket.AF_INET6, server_recv_addr) + struct.pack("=I", 0) # ifindex 设为 0

                # 使用 sendmsg() 来发送数据并指定源地址
                # (data, control_messages, flags, address)
                # control_messages 是一个列表，每个元素是 (cmsg_level, cmsg_type, cmsg_data)
                s.sendmsg(
                    [response],
                    [(socket.IPPROTO_IPV6, socket.IPV6_PKTINFO, pktinfo)],
                    0, # flags
                    (client_addr, client_port)
                )
                print(f"回复已从服务器本地地址 [{server_recv_addr}] 发送给 [{client_addr}]:{client_port}")
            else:
                print(f"收到来自 [{client_addr}]:{client_port} 的数据，但未能获取到目标 IP 信息。")
                # 备用：如果获取不到 PKTINFO，就直接回复，但可能出现源地址不一致问题
                response = b"Hello from server (no pktinfo)!"
                s.sendto(response, (client_addr, client_port))


def client_test_multiple_addrs(SERVER_HOST, SERVER_PORT = 6789):
    es = socket.getaddrinfo(SERVER_HOST, SERVER_PORT, socket.AF_UNSPEC, socket.SOCK_DGRAM)[0]
    inet, socktype, proto, canonname, sa = es

    with socket.socket(inet, socktype, proto) as s:

        message = b"Hello server, please reply to my source!"
        # 这里 SERVER_HOST 需要是服务器的一个有效 IPv6 地址，可以是任意一个
        # 因为服务器会从接收到数据包的那个地址进行回复
        s.sendto(message, (SERVER_HOST, SERVER_PORT))
        print(f"客户端发送数据到 [{SERVER_HOST}]:{SERVER_PORT}")

        s.settimeout(5) # 设置接收超时
        try:
            data, addr = s.recvfrom(1024)
            print(f"客户端收到来自 {addr} 的回复: {data.decode()}")
        except socket.timeout:
            print("客户端接收超时，未收到回复。请检查服务器日志。")
        except Exception as e:
            print(f"客户端接收出错: {e}")



# 封装成一个类试试
class IPv6UDPServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)  # 开启 IPV6_PKTINFO 选项
        self.sock.bind((self.host, self.port))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()

    def recv(self, buffer_size=8192) -> tuple[bytes, tuple]:
        data, ancdata, msg_flags, addr = self.sock.recvmsg(buffer_size, 1024)
        # 解析控制消息以获取目标地址信息
        for cmsg_level, cmsg_type, cmsg_data in ancdata:
            if cmsg_level == socket.IPPROTO_IPV6 and cmsg_type == socket.IPV6_PKTINFO:
                self.cmsg_level = cmsg_level
                self.cmsg_type = cmsg_type
                self.pktinfo = cmsg_data
                # self.server_recv_addr = socket.inet_ntop(socket.AF_INET6, cmsg_data[:16])
                # self.if_index = struct.unpack("=I", cmsg_data[16:20])[0]  # 如果需要接口索引
                return data, addr
        
        # 如果没有控制消息，直接返回数据和地址
        return data, addr 
    
    def send(self, data: bytes, addr: tuple) -> int:
        return self.sock.sendmsg([data], [(self.cmsg_level, self.cmsg_type, self.pktinfo)], 0, addr)



def server_with_pktinfo2():
    with IPv6UDPServer('::', 6789) as server:
        print(f"服务器已绑定到 [{server.host}]:{server.port} 并开启 IPV6_RECVPKTINFO")
        
        while True:
            data, addr = server.recv()
            print(f"收到来自 {addr} 的数据: {data.decode()}")

            response = b"Hello from server!"
            server.send(response, addr)
            print(f"回复已发送给 {addr}")


if __name__ == "__main__":

    if sys.argv[1] == 'server':
        server_with_pktinfo()

    elif sys.argv[1] == 'server2':
        server_with_pktinfo2()

    elif sys.argv[1] == 'client':
        if len(sys.argv) < 3:
            print("请提供服务器地址和端口，例如: python script.py client ::1 54321")
            sys.exit(1)

        SERVER_HOST = sys.argv[2]
        SERVER_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 6789
        print(f"客户端将连接到服务器 [{SERVER_HOST}]:{SERVER_PORT}")
        client_test_multiple_addrs( SERVER_HOST, SERVER_PORT)
    else:
        print("请指定 'server' 或 'client' 模式，例如: python script.py server 或 python script.py client")
        


