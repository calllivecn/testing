import asyncio
import time
import sys
import argparse
import httpx
import dns.message

# 使用 dnspython 构造标准的 DNS 查询报文
def create_dns_query(domain: str, typ: str):
    """
    构造针对指定域名的 A 记录查询报文
    """
    msg = dns.message.make_query(domain, 'A')
    return msg.to_wire()

class DoHBench:
    def __init__(self, resolver_url: str, domain: str, concurrency: int, total: int):
        self.resolver_url = resolver_url
        self.domain = domain
        self.concurrency = concurrency
        self.total = total
        self.results = []
        # 强制启用 HTTP/2 以模拟真实生产环境的 DoH 行为
        self.client = httpx.AsyncClient(http2=True, timeout=10.0)

    async def send_query(self, semaphore: asyncio.Semaphore, query_data: bytes):
        async with semaphore:
            headers = {
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
            }
            start = time.perf_counter()
            try:
                resp = await self.client.post(
                    self.resolver_url,
                    content=query_data,
                    headers=headers
                )
                latency = time.perf_counter() - start
                if resp.status_code == 200:
                    self.results.append(latency)
                else:
                    print(f"[-] HTTP Error {resp.status_code}", file=sys.stderr)
            except Exception as e:
                print(f"[-] Request Failed: {e}", file=sys.stderr)

    async def run(self, typ: str):
        query_data = create_dns_query(self.domain, typ)
        print(f"[*] Target Resolver: {self.resolver_url}")
        print(f"[*] Query Domain:    {self.domain} (Type {typ})")
        print(f"[*] Configuration:   Concurrency={self.concurrency}, Total={self.total}")
        
        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = [self.send_query(semaphore, query_data) for _ in range(self.total)]
        
        start_time = time.perf_counter()
        await asyncio.gather(*tasks)
        duration = time.perf_counter() - start_time
        
        await self.client.aclose()
        self._print_stats(duration)

    def _print_stats(self, duration):
        if not self.results:
            return
        
        self.results.sort()
        count = len(self.results)
        avg = sum(self.results) / count
        p95 = self.results[int(count * 0.95)]
        tps = count / duration

        print("\n" + "="*30)
        print(f"Summary Statistics:")
        print(f"  Success:     {count}/{self.total}")
        print(f"  Total Time:  {duration:.2f}s")
        print(f"  TPS:         {tps:.2f} req/s")
        print(f"  Avg Latency: {avg*1000:.2f} ms")
        print(f"  P95 Latency: {p95*1000:.2f} ms")
        print("="*30)

def main():
    parser = argparse.ArgumentParser(description="DoH 并发性能测试工具")
    parser.add_argument("--resolver", default="https://dns.alidns.com/dns-query", help="DoH 服务器地址, 如: https://dns.alidns.com/dns-query")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="并发数 (默认: 10)")
    parser.add_argument("-n", "--total", type=int, default=50, help="总请求数 (默认: 50)")
    parser.add_argument("-t", default="aaaa", help="查询类型：(A, AAAA) 默认：AAAA 不区分大小写")
    parser.add_argument("domain", help="要查询的域名, 如: www.google.com")

    args = parser.parse_args()

    try:
        dohb = DoHBench(args.resolver, args.domain, args.concurrency, args.total)
        asyncio.run(dohb.run(args.t))
    except KeyboardInterrupt:
        print("\n[!] 测试已由用户终止")

if __name__ == "__main__":
    main()
