#!/usr/bin/env python3
"""
XDG Desktop Portal 权限商店管理工具
基于 dbus-next 库，用于查看和管理系统的持久化授权记录（例如 screencast 的 restore_token）。
"""

import asyncio
import sys
import argparse
from dbus_next.aio.message_bus import MessageBus
from dbus_next import Message
from dbus_next.constants import BusType

# D-Bus 服务配置常量
BUS_NAME = 'org.freedesktop.impl.portal.PermissionStore'
OBJ_PATH = '/org/freedesktop/impl/portal/PermissionStore'
INTERFACE = 'org.freedesktop.impl.portal.PermissionStore'

async def call_dbus(bus: MessageBus, method: str, signature: str, body: list):
    """通用低级 D-Bus 方法调用封装"""
    msg = Message(
        destination=BUS_NAME,
        path=OBJ_PATH,
        interface=INTERFACE,
        member=method,
        signature=signature,
        body=body
    )
    reply = await bus.call(msg)
    return reply.body

async def cmd_list(bus: MessageBus, table: str):
    """列出指定权限表中的所有资源、应用映射及关联数据"""
    try:
        # 调用 List 获取表中所有资源 ID
        res = await call_dbus(bus, 'List', 's', [table])
        resource_ids = res[0]
        
        if not resource_ids:
            print(f"ℹ️  权限表 '{table}' 中目前没有任何记录。")
            return
        
        print(f"==================================================")
        print(f" 📂 权限表: {table} (共 {len(resource_ids)} 个资源项目)")
        print(f"==================================================")
        
        for r_id in resource_ids:
            print(f"\n📍 资源 ID (Object ID): '{r_id}'")
            
            # 查找具体资源的权限字典与关联 Variant 数据
            lookup_res = await call_dbus(bus, 'Lookup', 'ss', [table, r_id])
            permissions = lookup_res[0]  # 类型: a{sas} (App ID -> 权限列表)
            data_variant = lookup_res[1] # 类型: v (附加数据变体)
            
            # 1. 打印关联的应用权限
            print("  🔒 授权应用及状态:")
            if not permissions:
                print("    (无任何应用级授权记录)")
            for app_id, perms in permissions.items():
                # 空字符串代表未经过沙盒封装、未声明 App ID 的裸进程（如通过终端运行的 python 脚本）
                app_display = '"" [匿名脚本/终端原生进程]' if app_id == "" else f'"{app_id}"'
                print(f"    - 应用: {app_display}")
                print(f"      权限: {perms}")
            
            # 2. 打印并解析附加数据 (对于 screencast，这里存放着当前激活的 restore_token)
            print("  💾 附加持久化数据 (Data Variant):")
            if data_variant and data_variant.value is not None:
                val = data_variant.value
                # 针对 screencast 常见的结构进行扁平化和格式化展开
                if isinstance(val, list):
                    tokens = []
                    for item in val:
                        if isinstance(item, (list, tuple)):
                            tokens.extend([str(i) for i in item])
                        else:
                            tokens.append(str(item))
                    
                    if tokens:
                        print("    - 检测到系统中此资源激活的 Restore Token:")
                        for t in tokens:
                            print(f"      🔹 {t}")
                    else:
                        print("    - 数组为空 (无可用 Token)")
                else:
                    print(f"    - 原始值: {val} (类型: {type(val).__name__})")
            else:
                print("    - (无附加数据)")
        print(f"\n==================================================")

    except Exception as e:
        print(f"❌ 查询失败: {e}", file=sys.stderr)

async def cmd_delete(bus: MessageBus, table: str, resource_id: str, app_id: str = None):
    """删除指定资源记录或特定应用的单条权限项"""
    try:
        if app_id is not None:
            # 移除特定应用的授权（支持传入 "" 清理匿名进程）
            app_desc = '"" (匿名脚本)' if app_id == "" else f'"{app_id}"'
            print(f"🧹 正在从表 '{table}' 的资源 '{resource_id}' 中移除应用 {app_desc} 的权限...")
            await call_dbus(bus, 'DeletePermission', 'sss', [table, resource_id, app_id])
            print("✅ 应用授权单项移除成功！")
        else:
            # 移除该资源下的所有应用及关联的全部数据（如清空整个屏幕共享记录）
            print(f"🗑️ 正在完全销毁表 '{table}' 中资源 '{resource_id}' 的整条记录及所有绑定的 Token...")
            await call_dbus(bus, 'Delete', 'ss', [table, resource_id])
            print("✅ 资源记录完全清除成功！")
    except Exception as e:
        print(f"❌ 操作失败: {e}", file=sys.stderr)

async def amain(args):
    """异步入口，建立总线连接并分发路由"""
    # 连接到当前用户的 D-Bus Session 会话总线
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    
    if args.command == "list":
        await cmd_list(bus, args.table)
    elif args.command == "delete":
        await cmd_delete(bus, args.table, args.id, args.app)
        
    # 断开 D-Bus 连接释放资源
    bus.disconnect()

def main():
    parser = argparse.ArgumentParser(
        description="XDG Portal PermissionStore 命令行权限管理维护工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  1. 查看当前屏幕共享的所有授权和 Token 列表:
     python3 permission_manager.py list
  2. 查看相机等其他硬件的授权表:
     python3 permission_manager.py list --table devices
  3. 完全清空屏幕共享的授权记录以重新触发弹窗:
     python3 permission_manager.py delete --id screencast
  4. 仅清除屏幕共享记录中针对匿名 Python 脚本的分支权限:
     python3 permission_manager.py delete --id screencast --app ""
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用的管理操作指令")

    # 配置 list 子命令
    list_parser = subparsers.add_parser("list", help="读取并列出指定表中的权限及数据结构")
    list_parser.add_argument(
        "--table", 
        default="screencast", 
        help="目标权限表名称。默认值为 'screencast'。常用的还有: screenshot, devices 等"
    )

    # 配置 delete 子命令
    delete_parser = subparsers.add_parser("delete", help="删除或重置权限记录")
    delete_parser.add_argument(
        "--table", 
        default="screencast", 
        help="目标权限表名称。默认值为 'screencast'"
    )
    delete_parser.add_argument(
        "--id", 
        required=True, 
        help="要操作的目标资源 ID (例如，屏幕共享固定为 'screencast'，摄像头固定为 'camera')"
    )
    delete_parser.add_argument(
        "--app", 
        default=None, 
        help='指定要剥离权限的特定 App ID。如果要清理匿名 Python 运行历史，请传入空字符串 ""。不传此参数将清除此 ID 下的所有记录。'
    )

    args = parser.parse_args()
    try:
        asyncio.run(amain(args))
    except KeyboardInterrupt:
        print("\n操作已被用户中断。")
        sys.exit(1)

if __name__ == '__main__':
    main()
