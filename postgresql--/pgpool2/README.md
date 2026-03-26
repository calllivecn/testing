# PGPool-II 配置过程


- 要停止 Pgpool-II ，请执行：

    ```shell
    $ pgpool -m fast stop
    ```


## 在podman 中使用MacVLAN + 宿主机能和容器网络通信

```shell
# 1. 创建一个新的 macvlan 类型的接口，挂载在 br0 上
sudo ip link add link br0 name macv-host type macvlan mode bridge

# 2. 给这个接口分配一个局域网内的空闲 IP（不要和容器或路由器冲突）
# 例如使用 192.168.1.199
sudo ip addr add 192.168.1.199/24 dev macv-host

# 3. 启用接口
sudo ip link set macv-host up

# 4. 重点：设置路由，告诉宿主机访问容器 IP 范围时通过这个新接口
# 假设容器范围是 .208 到 .223
sudo ip route add 192.168.1.208/28 dev macv-host
```
