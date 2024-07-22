

__all__ = ("Users")

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def loadcfg(path: Path):
    with open(path, "rb") as f:
        return tomllib.load(f)


Users = loadcfg("user.toml")


