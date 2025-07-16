import dns.resolver

def query_with_custom_nameserver(domain, record_type, nameserver_ip):
    """
    使用指定的上游 nameserver 查询 DNS 记录。

    Args:
        domain (str): 要查询的域名。
        record_type (str): 要查询的记录类型 (例如 'A', 'MX', 'NS')。
        nameserver_ip (str): 要使用的 DNS 服务器的 IP 地址。

    Returns:
        list: 包含查询结果的列表，如果查询失败则返回空列表。
    """
    # 创建一个新的 Resolver 实例
    resolver = dns.resolver.Resolver()

    # 关闭自动配置，这样它就不会读取系统默认的 DNS 配置 (例如 /etc/resolv.conf)
    # 如果不设置 configure=False，dnspython 可能会在 nameservers 列表中添加系统默认的 DNS 服务器
    resolver.configure = False

    # 设置要使用的 nameserver IP 地址列表
    # 注意：nameservers 属性接受一个 IP 地址字符串列表
    resolver.nameservers = [nameserver_ip]

    try:
        # 使用配置好的 resolver 进行查询
        answers = resolver.resolve(domain, record_type)
        print(f"使用 nameserver {nameserver_ip} 查询 {domain} 的 {record_type} 记录:")
        results = []
        for rdata in answers:
            results.append(str(rdata))
            print(f"- {rdata}")
        return results
    except dns.resolver.NoAnswer:
        print(f"没有从 {nameserver_ip} 收到 {domain} 的 {record_type} 记录的答案。")
        return []
    except dns.resolver.NXDOMAIN:
        print(f"{domain} 不存在 (NXDOMAIN) 或无法从 {nameserver_ip} 解析。")
        return []
    except dns.exception.Timeout:
        print(f"查询 {domain} 到 {nameserver_ip} 超时。")
        return []
    except Exception as e:
        print(f"查询时发生错误: {e}")
        return []

if __name__ == "__main__":
    # 使用 Google Public DNS (8.8.8.8) 进行查询
    google_dns = "8.8.8.8"
    cloudflare_dns = "1.1.1.1"

    google_dns = "223.5.5.5"
    cloudflare_dns = "114.114.114.114"

    print("--- 使用 Google Public DNS ---")
    query_with_custom_nameserver("example.com", "A", google_dns)
    query_with_custom_nameserver("google.com", "MX", google_dns)

    print("\n--- 使用 Cloudflare DNS ---")
    query_with_custom_nameserver("github.com", "A", cloudflare_dns)
    query_with_custom_nameserver("wikipedia.org", "NS", cloudflare_dns)

    # 尝试一个不存在的域名
    print("\n--- 尝试查询一个不存在的域名 ---")
    query_with_custom_nameserver("nonexistent-domain-12345.com", "A", google_dns)

    # 你也可以指定多个 nameserver，resolver 会按顺序尝试
    print("\n--- 使用多个 nameserver ---")
    resolver_multi = dns.resolver.Resolver()
    resolver_multi.nameservers = ["8.8.8.8", "1.1.1.1", "9.9.9.9"] # Google, Cloudflare, Quad9
    try:
        answers = resolver_multi.resolve("baidu.com", "A")
        print("使用多个 nameserver 查询 baidu.com 的 A 记录:")
        for rdata in answers:
            print(f"- {rdata}")
    except Exception as e:
        print(f"使用多个 nameserver 查询时发生错误: {e}")
