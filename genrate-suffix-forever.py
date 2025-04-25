



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



from pathlib import Path
root = Path("/tmp/out")
root.mkdir(exist_ok=True)

gen = genrate_suffix("filename_prefix.")
for i in range(1200):
    filename = next(gen)
    f_p = root / filename
    print(f"create file: {f_p}")
    f_p.touch()


