
from dns import (
    query,
    message,
)

# 定义DoH服务器的URL
#doh_url = "https://dns.example.com/dns-query"
doh_url = "https://dns.alidns.com/dns-query"

# 创建一个DNS查询消息
domain = "www.tmall.com"
rr_type = "AAAA"
message = message.make_query(domain, rr_type)

# 使用DoH进行查询
response = query.https(message, where=doh_url)

# 打印解析结果
for answer in response.answer:
    print(answer)
