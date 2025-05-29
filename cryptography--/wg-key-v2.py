import os
import base64
from cryptography.hazmat.primitives.asymmetric import x25519

class WireGuardKeyGenerator:
    def __init__(self):
        """
        初始化 WireGuardKeyGenerator。
        私钥不会立即生成（直到调用 genkey() 方法）。
        """
        self._private_key_raw: bytes | None = None
        self._public_key_raw: bytes | None = None

    def genkey(self) -> str:
        """
        生成一个新的 WireGuard 私钥，并将其内部存储，
        然后返回其 Base64 编码表示。
        这等同于 `wg genkey` 命令。
        """
        self._private_key_raw = os.urandom(32)
        # 生成私钥时自动派生并存储公钥
        private_key_obj = x25519.X25519PrivateKey.from_private_bytes(self._private_key_raw)
        public_key_obj = private_key_obj.public_key()
        self._public_key_raw = public_key_obj.public_bytes_raw()
        return base64.b64encode(self._private_key_raw).decode('utf-8')

    def genpub(self) -> str:
        """
        返回与内部存储私钥对应的 Base64 编码公钥。
        调用此方法前必须先调用 `genkey()`。
        这等同于 `wg pubkey` 命令。
        """
        if self._private_key_raw is None or self._public_key_raw is None:
            raise ValueError("私钥尚未生成。请先调用 genkey()。")
        return base64.b64encode(self._public_key_raw).decode('utf-8')

    @staticmethod
    def genpsk() -> str:
        """
        生成一个新的 WireGuard 预共享密钥 (preshared key)，并返回其 Base64 编码表示。
        这等同于 `wg genpsk` 命令。
        此方法是静态的，因为它不依赖于实例的私钥/公钥对。
        """
        psk_raw = os.urandom(32)
        return base64.b64encode(psk_raw).decode('utf-8')

    # --- 可选：如果需要获取原始密钥字节，可以使用以下方法 ---
    def get_raw_private_key(self) -> bytes | None:
        """返回原始私钥字节。"""
        return self._private_key_raw

    def get_raw_public_key(self) -> bytes | None:
        """返回原始公钥字节。"""
        return self._public_key_raw


def main():
    print("正在使用 WireGuardKeyGenerator 类...\n")
    generator = WireGuardKeyGenerator()

    # --- 生成私钥和公钥 ---
    print("1. 正在生成私钥:")
    private_key_b64 = generator.genkey() # genkey 现在也生成并存储公钥
    print(f"    Base64 私钥: {private_key_b64}")
    # print(f"    原始私钥 (十六进制): {generator.get_raw_private_key().hex() if generator.get_raw_private_key() else 'N/A'}\n") # type: ignore

    print("2. 正在获取公钥:")
    public_key_b64 = generator.genpub()
    print(f"    Base64 公钥:  {public_key_b64}")
    # print(f"    原始公钥 (十六进制):  {generator.get_raw_public_key().hex() if generator.get_raw_public_key() else 'N/A'}\n") # type: ignore

    # --- 生成预共享密钥 ---
    print("3. 正在生成预共享密钥:")
    psk_b64 = WireGuardKeyGenerator.genpsk() # 作为静态方法调用
    # 或者： psk_b64 = generator.genpsk() 如果你更喜欢实例方法风格以保持一致性
    print(f"    Base64 预共享密钥: {psk_b64}\n")

    print("--- WireGuard 配置示例用法 ---")
    print(f"""
[Interface]
PrivateKey = {private_key_b64}
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = # 其他对端公钥在此处
PresharedKey = {psk_b64} # 可选
Endpoint = # 对端IP:端口
AllowedIPs = 10.0.0.2/32
""")

    # 尝试在生成私钥之前获取公钥的示例
    print("\n--- 测试：在生成私钥之前尝试获取公钥 ---")
    new_generator = WireGuardKeyGenerator()
    try:
        new_generator.genpub()
    except ValueError as e:
        print(f"错误，符合预期: {e}")


if __name__ == "__main__":
    # 确保你安装了 cryptography 库:
    # pip install cryptography
    main()
