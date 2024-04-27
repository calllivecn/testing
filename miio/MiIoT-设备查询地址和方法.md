# 使用方式

0. 使用 miiocli miotdevice --ip $MIROBO_IP --token $MIROBO_TOKEN info 命令查看设备 modul 类型, 如：Model: chuangmi.plug.m3

1. 在 MIOT 设备列表中找到您的设备：[所有小米IoT设备](https://miot-spec.org/miot-spec-v2/instances?status=all)

2. 搜索“cubee.airrtc.th123e”并找到以下行：
    ```json
    {"status": "released","model":"cubee.airrtc.th123e","version":1,"type":**"urn:miot-spec-v2:device:thermostat:0000A031:cubee-th123e:1"**}
    ```

3. 复制此网址后面的“urn”部分。

    就我而言：https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:outlet:0000A002:cuco-v3:1
    您将看到设备规格的未格式化 JSON 文本:

4. 您将看到一个包含服务列表（稍后用作“siid”）的层次结构，每个服务都有一个属性列表（“piid”）,您需要在列表中找到一些您想要从设备获取并且可读的属性。在我的例子中 siid 1 没有返回值，因此您可能需要检查其他服务，例如“siid 2”和其他属性
    
    ![0001](imgs/0001.png)

5. 我想接收当前的“目标温度”。这是“siid”：2和“piid”：5：

    ![0002](imgs/0002.png)

6. 尝试通过在终端中输入以下内容来获取设备的响应：
    ```shell
    miiocli -d device --ip $IP --token $TOKEN raw_command get_properties "[{'did': 'MYDID', 'siid': 2, 'piid': 5 }]"
    ```

    - 我收到了回复，最后一行是： "[{'did': 'MYDID', 'siid': 2, 'piid': 5, 'code': 0, 'value': 29}]"
    - 这是我的设备上设置的实际目标温度：29 摄氏度！

7. 现在让我们尝试更改一些属性。确保它具有“写入”访问权限（查看上述 JSON 文件中特定 piid 的“访问”字段）。 我想设置 28 度，命令如下：
    ```shell
    miiocli -d device --ip 192.168.1.152 --token b110204d86732b019d3d6axxxxb9ad3a raw_command set_properties "[{'did': 'MYDID', 'siid': 2, 'piid': 5, 'value' : 28 }]"
    ```
    - 新的温度已在我的设备上设置，并且也在 MiHome 应用程序中更新！