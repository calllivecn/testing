# 小米物联网python 库+命令工具

- 安装: pip install python-miio


## 查看当前设备IP+token

- 您可以使用 python-miio 库来控制小米智能设备。您需要知道设备的 IP 地址和 token。IP 地址可以在米家 APP 的设备控制界面查询：右上角…按钮，选择网络信息，可看到 IP 1。

- 获取 token 的方法有很多，最简单的方法是使用 miiocli 命令行工具的 cloud 命令，它可以从您的云帐户中获取 token 2。您可以使用以下命令：

```
miiocli cloud
```

- 然后按照提示输入您的用户名和密码。这将显示您帐户中所有设备的名称、型号、token 和 IP 地址。
