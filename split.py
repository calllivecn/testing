#!/usr/bin/env python3

import sys
import argparse

def parse_size(size_str):
    """Converts a size string (e.g., 10K, 1M, 2G) to bytes."""
    size_str = size_str.upper()
    unit = None
    if unit is None: # Check for K, M, G (powers of 1024) or b (512)
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
        elif size_str.lower().endswith('b'): # GNU 'b' for 512 block size
            unit = 512
            size_str = size_str[:-1]

    try:
        val = int(size_str)
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}{unit if unit else ''}")

    return val * unit if unit else val


def split_by_bytes(infile, prefix, bytes_per_file, verbose):
    """Splits the input file by a specified number of bytes."""
    file_count = 0
    bytes_written_current_file = 0
    outfile = None

    blocksize = 1<<20 # 1MB

    in_stream = sys.stdin.buffer if infile == '-' else open(infile, 'rb')

    try:
        while True:
            # 读取数据块
            chunk = in_stream.read(blocksize)
            if not chunk:
                break  # 读取到文件末尾

            # 如果当前文件未打开或已达到指定大小，则创建新文件
            if outfile is None or bytes_written_current_file >= bytes_per_file:
                if outfile:
                    outfile.close()
                out_filename = f"{prefix}.{file_count}"
                if verbose:
                    print(f"Creating file '{out_filename}'")
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


def main():
    parser = argparse.ArgumentParser(description="Split a file into pieces. Mimics some GNU split features.")
    parser.add_argument('input', nargs='?', default='-',
                        help="Input file (default: stdin, represented by '-')")
    parser.add_argument('prefix', nargs='?', default='data.',
                        help="Prefix for output file names (default: 'x')")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--bytes', type=str, default="512M",
                       help="Number of bytes per output file (e.g., 10K, 1M, 500). Suffixes: K,M,G,T,P (powers of 1024)")

    parser.add_argument('--separator', default='\n',
                        help="Line separator character (default: newline). Use '\\0' for NULL.")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Print a diagnostic to standard error just before each output file is opened.")

    args = parser.parse_args()


    try:
        byte_size = parse_size(args.bytes)
        if byte_size <= 0:
             parser.error("--bytes must result in a positive byte count.")
    except ValueError as e:
        parser.error(f"Invalid format for --bytes: {e}")

    return split_by_bytes(args.input, args.prefix, byte_size, args.verbose)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except ValueError as e: # Catch suffix generation errors that might escape main logic
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSplit operation interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(2)
