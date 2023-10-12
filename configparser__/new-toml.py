
import sys
import pprint


try:
    # py3.11 之后
    import tomllib
except ModuleNotFoundError:
    # py3.11 之前,  # pip install tomli
    import tomli as tomllib

with open(sys.argv[1], "rb") as f:
    conf = tomllib.load(f)

# print(f"{type(conf)=} --> {conf=}")

pprint.pprint(conf)

print(tomllib.__file__)
