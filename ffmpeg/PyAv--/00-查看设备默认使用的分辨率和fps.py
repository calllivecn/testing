
import sys

import av

try:
    video = sys.argv[1]
except IndexError:
    video = "/dev/video0"

cap = av.open(video)
print(f"{dir(cap)=} \n{cap=}")
stream = cap.streams[0]

width = stream.width
height = stream.height
fps = stream.average_rate

print(f"分辨率: {width}x{height}")
print(f"帧率: {fps} fps")

cap.close()


