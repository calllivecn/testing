import sys

def print_all_unicode_emojis():
    # 定义所有包含 Emoji 或图形符号的 Unicode 区块
    # 格式: (起始位, 结束位, "描述")
    # 注意：Python range 是左闭右开，所以循环时需要 +1
    emoji_ranges = [
        # --- 核心表情区 ---
        (0x1F600, 0x1F64F, "Emoticons (核心表情/笑脸)"),
        (0x1F300, 0x1F5FF, "Misc Symbols and Pictographs (杂项象形文字: 食物/动物/月亮等)"),
        (0x1F680, 0x1F6FF, "Transport and Map (交通与地图)"),
        (0x1F900, 0x1F9FF, "Supplemental Symbols (补充象形文字: 较新的表情)"),
        
        # --- 扩展区 (最新的表情通常在这里) ---
        (0x1FA70, 0x1FAFF, "Symb & Pictographs Ext-A (扩展A: 鹅/姜/粉红心等)"),
        # (0x1FCC0, 0x1FCCF, "Symb & Pictographs Ext-B (极新扩展区)"), # 目前大多为空，暂注释

        # --- 符号与装饰 ---
        (0x2600, 0x26FF, "Miscellaneous Symbols (杂项符号: 星座/天气/黑白符号)"),
        (0x2700, 0x27BF, "Dingbats (装饰符号: 剪刀/手指/对勾)"),
        (0x2B50, 0x2B59, "Misc Symbols (星星等)"), 
        (0x2300, 0x23FF, "Misc Technical (部分技术符号: 比如手表、键盘按钮)"),
        (0x2190, 0x21FF, "Arrows (箭头)"),
        (0x2900, 0x297F, "Supplemental Arrows-B"),

        # --- 游戏与棋牌 ---
        (0x1F000, 0x1F02B, "Mahjong Tiles (麻将牌)"),
        (0x1F030, 0x1F093, "Domino Tiles (多米诺骨牌)"),
        (0x1F0A0, 0x1F0F5, "Playing Cards (扑克牌)"),

        # --- 封闭字符 (用于按钮、国旗等) ---
        (0x1F1E6, 0x1F1FF, "Regional Indicator Symbols (区域指示符: 用于组合国旗 🇨🇳)"),
        (0x1F200, 0x1F2FF, "Enclosed Ideographic Supp (日文/中文方形按钮 🈲)"),
        (0x2460, 0x24FF, "Enclosed Alphanumerics (带圈数字/字母 ①)"),
        (0x3200, 0x32FF, "Enclosed CJK Letters (带圈汉字/月份)"),
    ]

    print(f"{'='*60}")
    print(f"正在输出全面版 Emoji 列表")
    print(f"注意：显示效果取决于您的系统字体和终端支持程度")
    print(f"{'='*60}\n")

    total_count = 0

    for start, end, desc in emoji_ranges:
        print(f"--- 区块: {desc} (U+{start:X} - U+{end:X}) ---")
        line_count = 0
        
        for i in range(start, end + 1):
            try:
                char = chr(i)
                # 过滤掉一些不可打印的控制字符，只保留可能是图形的
                if char.isprintable() or 0x1F000 <= i <= 0x1FFFF: 
                    print(char, end=" ")
                    line_count += 1
                    total_count += 1
                    
                    if line_count % 30 == 0:
                        print()
            except:
                pass
        print("\n") # 每个区块结束后换行

    print(f"{'='*60}")
    print(f"输出完成。共尝试输出约 {total_count} 个字符。")
    print(f"{'='*60}")

if __name__ == "__main__":
    # 强制设置标准输出为 UTF-8，防止 Windows 默认 GBK 报错
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass 
    
    print_all_unicode_emojis()
