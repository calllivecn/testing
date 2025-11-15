import os

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


"""
Parameters :

salt (bytes) –— 每个密码的盐值应该是唯一的（并且随机生成），建议长度为 16 字节或更长。
length (int) ——派生密钥所需的字节长度。
iterations (int) ——也称为遍历次数，用于调整运行时间，而无需考虑内存大小。
lanes (int) –— 要使用的通道（并行线程）数量。也称为并行度。
memory_cost (int) –– 要使用的内存量，单位为千字节 (kib)。1 千字节 (KiB) 等于 1024 字节。这必须至少为 8 * lanes 。
ad (bytes) —— 可选的关联数据。
secret (bytes) –– 可选的秘密数据；用于键值哈希。
"""

salt = os.urandom(16)

# derive
kdf = Argon2id(
    salt=salt,
    length=32,
    iterations=13,
    lanes=4,
    memory_cost=64 * 1024, # 64M 内存
    ad=None,
    secret=None,
)

key = kdf.derive(b"my great password")

print(f"{len(key)=} {type(key)=} {key=}")

# verify
kdf = Argon2id(
    salt=salt,
    length=32,
    iterations=13,
    lanes=4,
    memory_cost=64 * 1024,
    ad=None,
    secret=None,
)

result = kdf.verify(b"my great password", key)
print("kdf.verify() -> ", result)

