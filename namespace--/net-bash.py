import os
import sys
import errno

def run_in_new_netns(command="/bin/bash"):
    """
    在全新的网络命名空间中运行一个指定命令 (默认是 bash)。
    """
    # 1. 创建子进程
    # 子进程将继承父进程的所有资源，但之后会拥有自己独立的执行上下文。
    pid = os.fork()

    if pid == 0:
        # ---------- 这里是子进程的代码 ----------
        try:
            # 2. 创建新的网络命名空间
            # 这个调用会让当前(子)进程脱离原有的网络栈，
            # 之后它创建的任何进程都将属于这个新的、匿名的网络命名空间。
            os.unshare(os.CLONE_NEWNET)
            print(f"[子进程 PID: {os.getpid()}] 已成功创建新的网络命名空间。")

        except OSError as e:
            # 创建命名空间通常需要 root 权限 (CAP_SYS_ADMIN)
            if e.errno == errno.EPERM:
                print("错误: 权限不足。创建网络命名空间需要 root 权限。", file=sys.stderr)
            else:
                print(f"创建命名空间失败: {e}", file=sys.stderr)
            os._exit(1)  # 使用 os._exit 确保子进程干净退出，不触发父进程的清理逻辑

        try:
            # 3. 在新命名空间中执行目标命令
            # os.execvp 会用一个新进程完全替换当前子进程的内存镜像。
            # 这意味着 bash 将直接运行在这个全新的网络命名空间中。
            print(f"[子进程 PID: {os.getpid()}] 即将启动 '{command}' ...")
            os.execvp(command, [command])
            
        except OSError as e:
            print(f"无法执行 '{command}': {e}", file=sys.stderr)
            os._exit(1)

    elif pid > 0:
        # ---------- 这里是父进程的代码 ----------
        print(f"父进程 PID: {os.getpid()}，已创建子进程 PID: {pid}。")
        print("父进程仍在原来的网络命名空间中。等待子进程退出...")
        
        # 等待子进程结束，并获取其退出状态
        _, status = os.waitpid(pid, 0)
        exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
        print(f"子进程已退出，退出码: {exit_code}")
        
    else:
        # fork 失败
        print("错误: fork() 调用失败。", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 检查 Python 版本和平台
    if sys.version_info < (3, 12):
        print("错误: 此脚本需要 Python 3.12 或更高版本。", file=sys.stderr)
        sys.exit(1)
    if sys.platform != "linux":
        print("错误: 此脚本仅在 Linux 系统上有效。", file=sys.stderr)
        sys.exit(1)

    # 检查是否以 root 权限运行 (通常需要)
    if os.geteuid() != 0:
        print("警告: 创建网络命名空间通常需要 root 权限。如果执行失败，请尝试使用 sudo。", file=sys.stderr)

    run_in_new_netns("/bin/bash")
