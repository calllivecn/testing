


from dataclasses import dataclass


@dataclass
class Preson:
    h: int
    age: int
    sex: str


d = {}

zx = Preson(176, 26, "M")
zx2 = Preson(176, 26, "M")

print(zx)

print(zx.h)


print( zx == zx2) # True

d[1] = zx

print(f"{d[1]=}")