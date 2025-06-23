

from pyroute2 import NDB, IPRoute

def getifname_index(ifname):
    with NDB() as ndb:
        return ndb.interfaces[ifname]["index"]


def add_route_ifname(net, ifname):
    """
    0.0.0.0/0, ::/0 就是默认网络
    """
    with NDB() as ndb:
        try:
            ndb.routes.create(dst=net, oif=getifname_index(ifname)).commit()
        except KeyError:
            print("路由已经存在")
            return

def get_routes():
    with NDB() as ndb:
        print(f"{ndb.routes.summary()}")

def ifname_exists(net):
    with NDB() as ndb:
        via = ndb.routes[net]
        print(f"{via=}")

#ifname_exists("10.1.2.0/24")

add_route_ifname("10.1.2.0/24", "wg-route")
get_routes()



