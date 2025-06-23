

from pyroute2 import IPRoute

def add_default(ifname: str, table_id: int, fwmark: int):
    with IPRoute() as ipr:
        # 添加默认路由到指定的路由表
        # 命令: ip route add default dev <ifname> table <table_id>
        ipr.route('add',
                  dst='0.0.0.0/0',
                  oif=ipr.link_lookup(ifname=ifname)[0],  # 获取接口索引
                  table=table_id)
        print(f"Added default route via {ifname} to table {table_id}")



add_default("wg-route", 0x8123, 0x8123)
