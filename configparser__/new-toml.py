
import sys
import pprint


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

with open(sys.argv[1], "rb") as f:
    conf = tomllib.load(f)

# print(f"{type(conf)=} --> {conf=}")

pprint.pprint(conf)

print(tomllib.__file__)