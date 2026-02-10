
import sys
import av

filename = sys.argv[1]

try:
    # 1. 打开文件
    container = av.open(filename)
    
    # 2. 获取视频流
    video_stream = container.streams.video[0]
    
    # 3. 读取 extradata
    extradata = video_stream.codec_context.extradata
    
    print(f"文件: {filename}")
    print(f"编码格式: {video_stream.codec_context.name}")
    
    if extradata:
        print(f"✅ 找到 Extradata!")
        print(f"长度: {len(extradata)} 字节")
        # 以十六进制打印前 20 个字节进行验证
        print(f"数据头 (Hex): {extradata[:20].hex(' ')}")
        
        # 格式鉴定
        if extradata.startswith(b'\x01'):
            print("鉴定结果: 标准 hvcC 格式 (MKV/MP4 规范)")
        elif extradata.startswith(b'\x00\x00\x01') or extradata.startswith(b'\x00\x00\x00\x01'):
            print("鉴定结果: Annex-B 格式 (裸流格式)")
        else:
            print("鉴定结果: 未知格式")
    else:
        print("❌ 未找到 Extradata (为空)")

    container.close()

except Exception as e:
    print(f"发生错误: {e}")
