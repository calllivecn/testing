

import sys


def 水仙花数():
    for i in range(100,999 + 1):
        数 = str(i)
        和 = 0
        for n in 数:
            和 += int(n) ** 3

        if 和 == i:
            print("水仙花数：",i)


if __name__ == "__main__":
    水仙花数()
