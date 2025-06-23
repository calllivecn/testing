
from pprint import pprint

from pyroute2 import IPRoute

with IPRoute() as ipr:
    ipr.bind()  # <--- start listening for RTNL broadcasts
    while True:
        for message in ipr.get():  # receive the broadcasts
            print(f"="*20)
            pprint(message)
