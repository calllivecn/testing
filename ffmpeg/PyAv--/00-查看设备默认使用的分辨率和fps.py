
import av

cap = av.open('/dev/video0')
print(f"{dir(cap)=} \n{cap=}")
stream = cap.streams[0]

width = stream.width
height = stream.height
fps = stream.average_rate

print(f"分辨率: {width}x{height}")
print(f"帧率: {fps} fps")

cap.close()


