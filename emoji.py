import sys

def print_unicode_emojis():
    # 定义 Emoji 所在的常见 Unicode 区块范围
    # 范围来源：Unicode 标准
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons (表情符号)
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs (杂项符号和象形文字)
        (0x1F680, 0x1F6FF),  # Transport and Map Symbols (交通和地图符号)
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs (补充符号和象形文字)
        (0x2600, 0x26FF),    # Miscellaneous Symbols (杂项符号)
        (0x2700, 0x27BF),    # Dingbats (装饰符号)
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A (扩展A区，较新的表情)
    ]

    count = 0
    print("开始输出 Emoji (基于 Unicode 范围)...\n")

    for start, end in emoji_ranges:
        for i in range(start, end + 1):
            try:
                # 将数字转换为字符
                char = chr(i)
                print(char, end=" ")
                count += 1
                if count % 30 == 0:
                    print()
            except UnicodeEncodeError:
                # 忽略无法在当前终端编码的字符
                pass

    print(f"\n\n大约输出了 {count} 个字符 (包含部分未分配的空位)。")

if __name__ == "__main__":
    # 确保输出编码为 UTF-8 (防止 Windows 控制台报错)
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Python 版本较低可能不支持 reconfigure

    print_unicode_emojis()
