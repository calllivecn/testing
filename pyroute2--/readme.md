
- IFA\_FLAGS 对应关系（手动判断）：

```C
IFA_F_TEMPORARY     = 0x01
IFA_F_NODAD         = 0x02
IFA_F_OPTIMISTIC    = 0x04
IFA_F_DADFAILED     = 0x08
IFA_F_HOMEADDRESS   = 0x10
IFA_F_DEPRECATED    = 0x20
IFA_F_TENTATIVE     = 0x40
IFA_F_PERMANENT     = 0x80
IFA_F_MANAGETEMPADDR= 0x100
IFA_F_NOPREFIXROUTE = 0x200
```

- 详细说明：

| 标签名（ip a 中的显示）  | 标志位                            | 意义                                                          |
| --------------- | ------------------------------ | ----------------------------------------------------------- |
| `temporary`     | `IFA_F_TEMPORARY` (0x01)       | 该地址是临时地址（用于提升隐私），通常是基于 RFC 4941 隐私扩展生成的                     |
| `dynamic`       | `IFA_F_DYNAMIC` (0x02)         | 地址是通过动态机制（如 DHCPv6、SLAAC）分配的，不是静态配置的                        |
| `deprecated`    | `IFA_F_DEPRECATED` (0x20)      | 地址处于弃用状态，但尚未失效，不建议新连接使用                                     |
| `mngtmpaddr`    | `IFA_F_MANAGETEMPADDR` (0x100) | 通常表示这个地址由内核自动管理生成的临时地址（RFC 4941 中由 "mngtmpaddr" 控制是否生成临时地址） |
| `noprefixroute` | `IFA_F_NOPREFIXROUTE` (0x200)  | 地址不会自动安装前缀路由                                                |
| `permanent`     | `IFA_F_PERMANENT` (0x80)       | 永久地址（配置持久）                                                  |
| `tentative`     | `IFA_F_TENTATIVE` (0x40)       | 正在进行 DAD（重复地址检测）流程，暂时不可用                                    |
| `optimistic`    | `IFA_F_OPTIMISTIC` (0x04)      | 乐观地址，尚未通过 DAD 但可用于发包                                        |
| `dadfailed`     | `IFA_F_DADFAILED` (0x08)       | DAD 检测失败，地址冲突                                               |
| `home`          | `IFA_F_HOMEADDRESS` (0x10)     | 用于 Mobile IPv6 中的 home address                              |
| `nodad`         | `IFA_F_NODAD` (0x02)           | 地址不会进行 DAD 检测（和 `dynamic` 共用位，含义依场景不同）                      |

- ✅ 补充：这些 flags 来源在哪儿？

- Linux 内核网络栈中 include/uapi/linux/if_addr.h 中定义了这些 IFA_F_* 常量。

- iproute2 工具把这些 flags 以人类可读形式显示。

## 📘 各组合的常见含义（举例说明）

| 示例                                              | 含义                                    |
| ----------------------------------------------- | ------------------------------------- |
| `scope global temporary dynamic`                | SLAAC 生成的临时地址（隐私地址），可用，动态生成           |
| `scope global temporary deprecated dynamic`     | 临时地址，已弃用（preferred\_lft 为 0），不应再用于新连接 |
| `scope global dynamic mngtmpaddr noprefixroute` | 主地址（非临时），动态生成，允许内核自动生成临时地址，不添加前缀路由    |
| `scope link noprefixroute`                      | 链路本地地址，不带前缀路由                         |
| `scope global permanent`                        | 静态配置的地址，持久有效                          |



## Q&A

- 为什么ip a 输出的是有 dynamic 标记的？

```
✅ 答案：ip 命令中显示的 dynamic ≠ IFA_F_DYNAMIC 这个 flag
这是一个历史遗留的混淆点。

Linux 内核 & iproute2 的行为：
ip 命令把一些非 flags 字段的值 也格式化成 “标签” 显示，比如：

如果地址是通过 内核自动生成（SLAAC）或者 DHCPv6 的，ip 会显示 dynamic

但这不一定在 Netlink 消息的 ifa_flags 里设置了 IFA_F_DYNAMIC (0x2)
```
