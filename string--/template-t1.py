from string import Template

# 1. 模拟你从认证服务器和启动器配置中获取到的真实数据
context = {
    "auth_player_name": "Steve",
    "version_name": "1.21.x",
    "game_directory": "C:/.minecraft",
    "assets_root": "C:/.minecraft/assets",
    "assets_index_name": "1.21",
    "auth_uuid": "00000000-0000-0000-0000-000000000000",
    "auth_access_token": "mock_token_123456",
    "clientid": "launcher_id",
    "auth_xuid": "0",
    "version_type": "release"
}

# 2. 从 JSON 里解析出来的原始参数列表（示例一段）
raw_game_args = [
    "--username", "${auth_player_name}/这是玩家名",
    "--version", "${version_name}",
    "--gameDir", "${game_directory}"
]

# 3. 遍历并利用 Template 进行替换
final_game_args = []
for arg in raw_game_args:
    # 使用 safe_substitute 可以防止某些未定义的变量导致程序崩溃，而是保留原样 ${xxx}
    processed_arg = Template(arg).safe_substitute(context)
    final_game_args.append(processed_arg)

print(final_game_args)
# 输出: ['--username', 'Steve', '--version', '1.21.x', '--gameDir', 'C:/.minecraft']


t2 = Template(" ".join(raw_game_args))

print(t2.safe_substitute(context))
