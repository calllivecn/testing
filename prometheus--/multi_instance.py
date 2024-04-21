
import time
import random

from prometheus_client import (
    start_http_server,
    Gauge,
    Info,
)

LN=["instance"]

info = Info("Multi_node_monitor", "随变写个描述，差不多了，")

info.info({"name": "测试我实例监控方式", "version": "0.1", "date": "2024-04-20"})

gauge = Gauge('multi_metric', '多指标', labelnames=LN)


start_http_server(8000)


while True:

    # 模拟从每个实例获取连接数
    gauge.labels(instance="instance1").set(random.randint(0, 100))
    gauge.labels(instance="instance2").set(random.randint(0, 100))

    time.sleep(5)
