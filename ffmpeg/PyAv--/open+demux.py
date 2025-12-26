
from fractions import Fraction

import av


# 这样封装是对的了, 但是没有 时间戳 播放是很快的。
def test1():
    input_container = av.open("output.h265", format="hevc")
    output_container = av.open("out.mkv", mode="w")

    in_stream = input_container.streams.video[0]
    out_stream = output_container.add_stream("hevc")

    for packet in input_container.demux(in_stream):
        packet.stream = out_stream
        output_container.mux(packet)

    output_container.close()


def test2():
    """
    能用的前提：
    
    """
    input_container = av.open("output.h265", format="hevc")
    output_container = av.open("out.mkv", mode="w")

    fps = 30
    time_base = Fraction(1, fps)

    in_stream = input_container.streams.video[0]

    extradata = in_stream.codec_context.extradata
    extradata_size = in_stream.codec_context.extradata_size
    print(f"{extradata_size=} {extradata=}")


    # 3. 正确 add_stream（重点）
    out_stream = output_container.add_stream("hevc")
    out_stream.time_base = time_base

    # 可选但强烈建议：拷贝参数
    out_stream.codec_context.width = in_stream.codec_context.width
    out_stream.codec_context.height = in_stream.codec_context.height
    out_stream.codec_context.pix_fmt = in_stream.codec_context.pix_fmt

    pts = 0
    for packet in input_container.demux(in_stream):
        print(f"{packet=} {packet.is_keyframe=} --> ", end="")
        packet.pts = pts
        packet.dts = pts
        packet.duration = 1
        packet.time_base = time_base
        packet.stream = out_stream

        print(f"{packet=} {packet.is_keyframe=}")

        output_container.mux(packet)
        pts += 1

    output_container.close()


if __name__ == "__main__":
    # test1()
    test2()