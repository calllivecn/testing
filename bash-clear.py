
import sys

clear = 0x1b.to_bytes(1, byteorder="big") + b"c"
clear = 0o33.to_bytes(1, byteorder="big") + b"c"

sys.stdout.buffer.write(clear)

