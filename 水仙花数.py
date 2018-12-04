

import sys


def 水仙花数(end=9999):

    for i in range(end):
        数 = str(i)
        数位 = len(数)
        和 = 0
        for n in 数:
            和 += int(n) ** 数位

        if 和 == i:
            print("水仙花数：",i)


if __name__ == "__main__":
    水仙花数(99995)
