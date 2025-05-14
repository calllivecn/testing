

from pathlib import Path


def genrate_suffix(prefix, width=2):
    file_index = 0
    width_current_max = int("9"*width)
    while True:

        suffix = str(file_index).zfill(width)
        files = f"{prefix}{suffix}"
        yield files

        file_index += 1
        if file_index > width_current_max:
            file_index = int("9"*width + "0"*width)
            # 数位翻倍
            width = width<<1
            width_current_max = int("9"*width)




def test():
    root = Path("/tmp/out")
    root.mkdir(exist_ok=True)

    gen = genrate_suffix("filename_prefix.")
    for i in range(1200):
        filename = next(gen)
        f_p = root / filename
        print(f"create file: {f_p}")
        f_p.touch()




def generate_suffix2(prefix: str, index: int, base_chars: str = "0123456789abcdefghijklmnopqrstuvwxyz") -> str:
    """
    根据索引生成紧凑的动态后缀，使用自定义字符集。
    :param prefix: 文件名前缀
    :param index: 当前文件的索引（从 0 开始）
    :param base_chars: 用于生成后缀的字符集（默认使用 0-9 和 a-z）
    :return: 紧凑的文件名后缀（如 'filename_prefix.0', 'filename_prefix.a', 'filename_prefix.10'）
    """
    base = len(base_chars)
    suffix = []

    # 将索引转换为指定字符集的表示
    while True:
        suffix.append(base_chars[index % base])
        index //= base
        if index == 0:
            break

    # 反转列表并拼接成字符串
    return f"{prefix}{''.join(reversed(suffix))}"


def test2():
    root = Path("/tmp/out")
    root.mkdir(exist_ok=True)

    base_chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    prefix = "filename_prefix."

    for i in range(1200):
        filename = generate_suffix2(prefix, i, base_chars)
        f_p = root / filename
        print(f"create file: {f_p}")
        f_p.touch()


if __name__ == "__main__":
    # test()
    test2()