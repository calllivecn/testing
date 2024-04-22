# 小米物联网python 库+命令工具

- 安装: pip install python-miio
- ~~[小米IoT设备信息](https://home.miot-spec.com/)~~
- [siid, piid 的使用方式](!MiIoT-设备查询地址和方法.md)



## 查看当前设备IP+token

- 您可以使用 python-miio 库来控制小米智能设备。您需要知道设备的 IP 地址和 token。IP 地址可以在米家 APP 的设备控制界面查询：右上角…按钮，选择网络信息，可看到 IP 1。

- 获取 token 的方法有很多，最简单的方法是使用 miiocli 命令行工具的 cloud 命令，它可以从您的云帐户中获取 token 2。您可以使用以下命令：

- 然后按照提示输入您的用户名(小米账号id)和密码。这将显示您帐户中所有设备的名称、型号、token 和 IP 地址。

```shell
$ miiocli cloud
```

- 还可以使用编程API的方式：

```python
from miio.cloud import CloudInterface

ci = CloudInterface(username="user", password="...")
devs = ci.get_devices()
for did, dev in devs.items():
    print(did)
    print(dev)

did='xxxxxx'
CloudDeviceInfo(did='xxxxxx', token='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', name='小米米家智能插座WiFi版', model='chuangmi.plug.m3', ip='192.168.1.X', description='设备在线 ', parent_id='', ssid='wifiname', mac='xx:xx:xx:xx:xx', locale=['cn'])

```




# 状态图

|         | 开   | 关   |
| ------- | ---- | ---- |
| 电量<=70 | 不动 | 打开 |
| 电量>=80 | 关闭 | 不动 |


<style>
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}
</style>
