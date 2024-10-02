
from typing import (
    List,
)

import sys

import av
from av.container import (
    Container,
)


out_filename = sys.argv[1]

in_filenames = sys.argv[:2]


def copy_stream():
    pass



def merge(out_container: Container, in_containers: List[Container]):

    # 在新文件里打开新的流
    out_streams = {}

    for s in in_container.streams:
        print(f"stream: {s} type:{s.type}")
        out_streams[s.type] = out_container.add_stream(template=s)


    for in_ in in_filenames:


