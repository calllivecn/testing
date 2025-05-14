#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

def parse_size(size_str):
    """将大小字符串（例如 10K、1M、2G）转换为字节数。"""
    size_str = size_str.upper()
    unit = None
    if unit is None:  # 检查 K、M、G（1024 的幂）或 b（512）
        if size_str.endswith('K'):
            unit = 1024
            size_str = size_str[:-1]
        elif size_str.endswith('M'):
            unit = 1024**2
            size_str = size_str[:-1]
        elif size_str.endswith('G'):
            unit = 1024**3
            size_str = size_str[:-1]
        elif size_str.endswith('T'):
            unit = 1024**4
            size_str = size_str[:-1]
        elif size_str.endswith('P'):
            unit = 1024**5
            size_str = size_str[:-1]
        elif size_str.lower().endswith('b'):  # GNU 'b' 表示 512 块大小
            unit = 512
            size_str = size_str[:-1]

    try:
        val = int(size_str)
    except ValueError:
        raise ValueError(f"无效的大小格式：{size_str}{unit if unit else ''}")

    return val * unit if unit else val

CHUNK_SIZE = 1<<20  # 每次读取的块大小（1M）

class FileSplitterMerger:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def split_by_bytes(self, infile, prefix, bytes_per_file):
        """按指定的字节数将输入文件拆分为多个文件。"""
        file_count = 0
        bytes_written_current_file = 0
        outfile = None

        blocksize = min(CHUNK_SIZE, bytes_per_file)  # 动态调整 blocksize，确保不超过 bytes_per_file

        in_stream = sys.stdin.buffer if infile == '-' else open(infile, 'rb')

        try:
            while True:
                # 读取数据块
                chunk = in_stream.read(blocksize)
                if not chunk:
                    break  # 读取到文件末尾

                while chunk:  # 确保 chunk 被完全处理
                    # 如果当前文件未打开或已达到指定大小，则创建新文件
                    if outfile is None or bytes_written_current_file >= bytes_per_file:
                        if outfile:
                            outfile.close()
                        out_filename = f"{prefix}.{file_count}"  # 使用零填充的编号
                        if self.verbose:
                            print(f"正在创建文件 '{out_filename}'")
                        outfile = open(out_filename, 'wb')
                        file_count += 1
                        bytes_written_current_file = 0

                    # 写入数据到当前文件
                    write_size = min(len(chunk), bytes_per_file - bytes_written_current_file)
                    outfile.write(chunk[:write_size])
                    bytes_written_current_file += write_size

                    # 如果当前块未完全写入，则将剩余部分保留到下一轮
                    chunk = chunk[write_size:]

        finally:
            if outfile:
                outfile.close()
            if infile != '-' and in_stream:
                in_stream.close()

        return 0

    def merge(self, prefix, output_file=None):
        """将具有指定前缀的多个文件合并为一个文件。"""

        out_stream = sys.stdout.buffer if output_file is None else open(output_file, 'wb')

        try:
            file_generator = self.__file_generator(prefix)
            while True:
                file = next(file_generator)
                if self.verbose:
                    print(f"正在合并文件 '{file}'")
                with open(file, 'rb') as infile:
                    while chunk := infile.read(CHUNK_SIZE):  # 每次读取 8KB
                        out_stream.write(chunk)
        except Exception as e:
            print(f"debug: {e}", file=sys.stderr)

        finally:
            if output_file is not None:
                out_stream.close()

    def __file_generator(self, prefix):
        """生成器：按后缀递增顺序生成文件名"""
        index = 0
        while True:
            file_name = Path(f"{prefix}.{index}")
            if self.verbose:
                print(f"检查文件 '{file_name}'")

            if not file_name.exists():
                raise ValueError(f"{file_name}: 文件不存在，停止合并。")

            yield file_name
            index += 1


def main():
    parser = argparse.ArgumentParser(description="将文件拆分为多个部分或合并文件。模仿 GNU split 的某些功能。")
    parser.add_argument('input', nargs='?', default='-',
                        help="输入文件（默认：标准输入，用 '-' 表示）")
    parser.add_argument('prefix', nargs='?', default='data',
                        help="输出文件名的前缀（默认：'data'）")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--bytes', type=str, default="512M",
                       help="每个输出文件的字节数（例如 10K、1M、500）。后缀：K,M,G,T,P（1024 的幂）")
    group.add_argument('-m', '--merge', action='store_true',
                       help="将具有指定前缀的文件合并为一个文件。")

    parser.add_argument('--separator', default='\n',
                        help="行分隔符字符（默认：换行符）。使用 '\\0' 表示 NULL。")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="在每个输出文件打开之前打印诊断信息到标准错误。")

    parser.add_argument('-o', '--output', type=str,
                        help="合并操作的输出文件（默认：标准输出）。")
        
    parser.add_argument('--parse', action='store_true',
                        help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.parse:
        # 解析参数
        print(f"{args=}")
        sys.exit(0)

    splitter_merger = FileSplitterMerger(verbose=args.verbose)

    try:
        if args.merge:
            # splitter_merger.merge(args.prefix, args.output)
            splitter_merger.merge(args.input, args.output)
        else:
            byte_size = parse_size(args.bytes)
            if byte_size <= 0:
                parser.error("--bytes 必须是一个正的字节数。")
            splitter_merger.split_by_bytes(args.input, args.prefix, byte_size)
    except ValueError as e:
        parser.error(f"--bytes 的格式无效：{e}")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ValueError as e:  # 捕获可能未被主逻辑捕获的后缀生成错误
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用户中断。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"发生了意外错误：{e}", file=sys.stderr)
        sys.exit(2)
