


class One:
    count = 0
    count2 = 0

    def __init__(self):
        self.add()

        One.count2 += 1
        print(f"当前已经创建了：{self.count=}, {self.count2=}")

    @classmethod
    def add(cls):
        cls.count += 1

    @classmethod
    def show(cls):
        print(f"当前已经创建了：{cls.count=}, {cls.count2=}")

# 这两种都可以

a = One()
a.show()
b = One()
b.show()
One()
b.show()
One()
b.show()