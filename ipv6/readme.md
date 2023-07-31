

ICMP 数据包格式如下：

```
| 字段 | 长度 | 描述 |
|---|---|---|
| 类型 | 1 字节 | ICMP 数据包的类型。 |
| 代码 | 1 字节 | ICMP 数据包的代码。 |
| 校验和 | 2 字节 | ICMP 数据包的校验和。 |
| 标识符 | 2 字节 | ICMP 数据包的标识符。 |
| 序号 | 2 字节 | ICMP 数据包的序号。 |
| 数据 | 0-65535 字节 | ICMP 数据包的数据。 |
```

ICMP 类型字段指定了 ICMP 数据包的类型。ICMP 类型值可能为 0 到 255。

ICMP 代码字段指定了 ICMP 数据包的代码。ICMP 代码值可能为 0 到 127。

ICMP 校验和字段用于验证 ICMP 数据包的完整性。校验和是通过计算数据包头和数据的校验和来计算的。

ICMP 标识符字段用于标识 ICMP 数据包。标识符是发送方分配给 ICMP 数据包的值。

ICMP 序号字段用于跟踪 ICMP 数据包。序号是发送方分配给 ICMP 数据包的值。

ICMP 数据字段用于携带 ICMP 数据。ICMP 数据字段的大小可能为 0 到 65535 字节。

以下是一些常见的 ICMP 数据包类型：

* ICMP Echo Request：用于测试网络连接。
* ICMP Echo Reply：用于响应 ICMP Echo Request。
* ICMP Destination Unreachable：用于表示数据包无法到达目的地。
* ICMP Time Exceeded：用于表示数据包在传输过程中超时。
* ICMP Port Unreachable：用于表示数据包无法到达目的地的端口。
* ICMP Source Quench：用于表示发送方发送的数据包太快。
* ICMP Redirect：用于告知发送方将数据包发送到另一个路由器。
* ICMP Information Request：用于请求网络信息。
* ICMP Information Reply：用于响应 ICMP Information Request。

使用 Python 构建 ICMP 数据包，可以使用 `scapy` 库。`scapy` 是一个 Python 库，用于构造和发送网络数据包。要使用 `scapy` 构造 ICMP 数据包，可以使用以下代码：

```
import scapy.all as scapy

# 创建 ICMP Echo Request 数据包
packet = scapy.IP(dst="www.google.com")/scapy.ICMP(type=8)

# 发送数据包
scapy.send(packet)
```

这个代码将会创建一个 ICMP Echo Request 数据包，目的地是 `www.google.com`。然后，它将会发送数据包。

`scapy` 库可以用于构造各种类型的 ICMP 数据包，包括 Echo Request、Echo Reply、Time Exceeded、Destination Unreachable、Redirect、Source Quench、Internet Control Message、Address Mask Reply 等。

有关 `scapy` 库的更多信息，请参阅 scapy 文档: https://scapy.readthedocs.io/en/latest/。