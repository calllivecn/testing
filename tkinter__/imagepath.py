

import sys
from pathlib import Path


__all__ = ("IMG_PATH")


p = Path(sys.argv[0]).parent


with open(p / "imagepath.conf") as f:
    IMG_PATH = f.read()
