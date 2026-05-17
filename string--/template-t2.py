from string import Template

def replace_placeholders(data, ctx):
    """
    递归替换复杂数据结构（dict/list/str）中所有的 ${变量}
    """
    if isinstance(data, str):
        # 如果是字符串，直接通过模板引擎替换
        return Template(data).safe_substitute(ctx)
    elif isinstance(data, list):
        # 如果是列表，递归处理每一个元素
        return [replace_placeholders(item, ctx) for item in data]
    elif isinstance(data, dict):
        # 如果是字典，递归处理所有的 key 和 value（不过通常只需要处理 value）
        return {k: replace_placeholders(v, ctx) for k, v in data.items()}
    else:
        # 数字、布尔值等基本类型直接返回
        return data

# ================= 实际测试 =================

# 模拟包含了规则对象的复杂游戏参数片段
mock_json_fragment = [
    "--username", "${auth_player_name}",
    {
        "rules": [],
        "value": ["--width", "${resolution_width}", "--height", "${resolution_height}"]
    }
]

# 核心上下文变量
my_context = {
    "auth_player_name": "Alex",
    "resolution_width": "1920",
    "resolution_height": "1080"
}

# 整体一键替换
clean_data = replace_placeholders(mock_json_fragment, my_context)
print(clean_data)
# 输出: ['--username', 'Alex', {'rules': [], 'value': ['--width', '1920', '--height', '1080']}]
