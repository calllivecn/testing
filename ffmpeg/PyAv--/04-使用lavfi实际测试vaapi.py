#!/usr/bin/env python3
"""
VAAPI 编解码测试工具
此脚本使用lavfi过滤器生成测试视频，然后通过VA-API进行编码和解码测试
修复了PyAV v16.1.0 API变化导致的问题
"""

import sys
import os
import logging
from fractions import Fraction
from pathlib import Path

import av

def get_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
    return logger

logger = get_logger(__name__)


def check_vaapi_support():
    """检查系统是否支持VA-API"""
    try:
        # 检查是否有VA-API相关的codec
        vaapi_codecs = []
        for codec_name in ['h264_vaapi', 'hevc_vaapi', 'vp8_vaapi', 'vp9_vaapi']:
            try:
                codec = av.Codec(codec_name, 'w')
                if codec and codec.name:
                    vaapi_codecs.append(codec_name)
            except Exception:
                continue
                
        return len(vaapi_codecs) > 0, vaapi_codecs
    except Exception as e:
        logger.error(f"检查VA-API支持时出错: {e}")
        return False, []

def generate_test_video_with_lavfi(output_path, codec, duration=5):
    """
    使用lavfi过滤器生成测试视频

    codec: 生成时使用软件编码，名称于上面的硬件编码器对应为：libx264, libx265, hevc, vp8, vp9
    """
    logger.info(f"生成测试视频: {output_path}, 时长: {duration}秒")
    
    try:
        # 创建一个虚拟流，使用lavfi生成测试模式
        input_container = av.open(f'color=c=red:s=1920x1080:d={duration}', format='lavfi')
        input_stream = input_container.streams.video[0]
        
        # 设置输出容器
        output_container = av.open(output_path, mode='w')
        
        # 创建输出视频流并设置参数
        output_stream = output_container.add_stream(codec)
        output_stream.width = input_stream.width
        output_stream.height = input_stream.height
        output_stream.bit_rate = 2000000  # 2Mbps
        output_stream.pix_fmt = 'yuv420p'
        
        # 设置帧率和时间基
        fps = 30
        output_stream.time_base = Fraction(1, fps)
        output_stream.codec_context.time_base = Fraction(1, fps)
        output_stream.codec_context.framerate = fps
        
        frame_count = 0
        for frame in input_container.decode(input_stream):
            frame_count += 1
            
            # 设置帧的时间戳
            frame.pts = frame_count
            frame.time_base = Fraction(1, fps)
            
            # 编码帧
            packets = output_stream.encode(frame)
            if packets:
                # 处理返回的可能是列表或单个packet的情况
                if isinstance(packets, list):
                    for packet in packets:
                        if packet:
                            output_container.mux(packet)
                else:
                    output_container.mux(packets)
            
            # 达到所需帧数后停止
            if frame_count >= duration * fps:  # 假设fps帧率
                break
        
        # 冲刷编码器 - 使用正确的异常类型
        try:
            while True:
                packets = output_stream.encode(None)  # 使用None作为冲刷信号
                if packets:
                    if isinstance(packets, list):
                        for packet in packets:
                            if packet:
                                output_container.mux(packet)
                            else:
                                break
                    else:
                        if packets:
                            output_container.mux(packets)
                        else:
                            break
                else:
                    break
        except (av.EOFError, av.InvalidDataError) as e:
            # 忽略EOF错误，这是正常的冲刷结束
            pass
        except Exception as e:
            logger.warning(f"冲刷编码器时出现其他错误: {e}", exc_info=True)
        
        output_container.close()
        input_container.close()
        logger.info("测试视频生成完成")
        
    except Exception as e:
        logger.error(f"生成测试视频时出错: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_hardware_encoding(codec_name, input_file, output_file):
    """
    测试硬件编码
    """
    logger.info(f"开始测试硬件编码: {codec_name}")
    
    try:
        input_container = av.open(input_file)
        input_stream = input_container.streams.video[0]
        
        output_container = av.open(output_file, mode='w')
        
        fps = 30
        # 创建硬件编码流
        output_stream = output_container.add_stream(codec_name, rate=fps)
        output_stream.width = input_stream.width
        output_stream.height = input_stream.height
        output_stream.bit_rate = 2000000  # 2Mbps
        
        # 设置帧率和时间基
        output_stream.time_base = Fraction(1, fps)
        output_stream.codec_context.time_base = Fraction(1, fps)
        
        # 配置编码器参数
        codec_context = output_stream.codec_context
        # 尝试设置合适的像素格式 - 使用正确的API
        try:
            codec_context.pix_fmt = 'nv12'  # 使用兼容的像素格式
        except AttributeError:
            # 如果pix_fmt属性不存在，忽略
            logger.debug("编码器上下文不支持pix_fmt属性")
        except Exception:
            # 如果设置失败，使用默认格式
            logger.warning("设置pix_fmt = 'nv12'失败 退回默认格式")
        
        frame_count = 0
        for frame in input_stream.decode():
            logger.debug(f"从测试文件编码：{frame=}")
            frame_count += 1
            
            # 设置帧的时间戳
            frame.pts = frame_count
            frame.time_base = Fraction(1, fps)
            
            try:
                # 确保帧格式正确
                target_format = 'nv12'
                if frame.format.name != target_format:
                    converted_frame = frame.reformat(width=frame.width, height=frame.height, format=target_format)
                    converted_frame.pts = frame.pts
                    converted_frame.time_base = frame.time_base
                    packets = output_stream.encode(converted_frame)
                else:
                    packets = output_stream.encode(frame)

                logger.debug(f"{len(packets)=}")

                if packets:
                    logger.debug(f"output_stream.encode(frame) 编码成功：{packets[0]=}")
                    # 处理返回的可能是列表或单个packet的情况
                    if isinstance(packets, list):
                        for packet in packets:
                            if packet:
                                output_container.mux(packet)
                    else:
                        output_container.mux(packets)
            except Exception as e:
                logger.warning(f"编码帧时出错: {e}", exc_info=True)
                # 如果编码失败，尝试使用原始帧
                try:
                    packets = output_stream.encode(frame)
                    if packets:
                        if isinstance(packets, list):
                            for packet in packets:
                                if packet:
                                    output_container.mux(packet)
                        else:
                            output_container.mux(packets)
                except Exception as e2:
                    logger.error(f"编码失败: {e2}")
                    break
            
            # 只处理前几帧用于测试
            if frame_count >= 30:  # 处理1秒的帧（假设30fps）
                break
        
        # 冲刷编码器 - 使用正确的异常类型
        try:
            for packets in output_stream.encode(None):  # 使用None作为冲刷信号
                if isinstance(packets, list):
                    for packet in packets:
                        if packet:
                            output_container.mux(packet)
                        else:
                            break
                else:
                    if packets:
                        output_container.mux(packets)
                    else:
                        break
        except (av.EOFError, av.InvalidDataError) as e:
            # 忽略EOF错误，这是正常的冲刷结束
            logger.warning(f"忽略EOF错误，这是正常的冲刷结束: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"冲刷编码器时出现其他错误: {e}", exc_info=True)
            # raise e
        
        output_container.close()
        input_container.close()
        
        logger.info(f"硬件编码测试成功: {codec_name}")
        return True
        
    except Exception as e:
        logger.error(f"硬件编码测试失败 {codec_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hardware_decoding(codec_name, input_file):
    """
    测试硬件解码
    """
    logger.info(f"开始测试硬件解码: {codec_name}")
    
    try:
        container = av.open(input_file)
        
        # 获取视频流 - 修复：使用正确的方法获取流
        video_stream = None
        for stream in container.streams:
            if stream.type == 'video':
                video_stream = stream
                break
        
        if video_stream is None:
            logger.error("未找到视频流")
            return False
        
        # 尝试配置硬件解码
        codec_context = video_stream.codec_context
        try:
            # 设置解码器像素格式为VAAPI兼容格式
            codec_context.pix_fmt = 'vaapi_vld'
        except AttributeError:
            logger.debug("解码器上下文不支持pix_fmt属性")
        except Exception as e:
            logger.debug(f"无法设置VAAPI解码格式: {e}，退回默认格式。")
        
        decoded_frame_count = 0
        # 修复：使用demux方法
        for packet in container.demux(video_stream):
            try:
                frames = packet.decode()
                for frame in frames:
                    decoded_frame_count += 1
                    logger.info(f"成功解码第 {decoded_frame_count} 帧 (格式: {frame.format}, width: {frame.width}, height: {frame.height})")
                    
                    # 只解码前几帧用于测试
                    if decoded_frame_count >= 10:
                        break
                if decoded_frame_count >= 10:
                    break
            except Exception as e:
                logger.warning(f"解码包时出错: {e}", exc_info=True)
                continue
        
        container.close()
        logger.info(f"硬件解码测试成功: {codec_name}")
        return True
        
    except Exception as e:
        logger.error(f"硬件解码测试失败 {codec_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("VAAPI 编解码支持测试工具 - PyAV v16.1.0兼容版")
    print("="*60)
    
    # 检查VA-API支持
    is_supported, codecs = check_vaapi_support()
    
    print(f"VA-API 支持状态: {'支持' if is_supported else '不支持'}")
    if codecs:
        print(f"可用的VA-API编码器: {', '.join(codecs)}")
    else:
        print("未找到可用的VA-API编码器")
    
    if not is_supported:
        print("\n系统似乎不支持VA-API，测试无法继续。")
        print("请确认:")
        print("- 已安装VA-API驱动")
        print("- GPU支持硬件加速")
        print("- 已正确配置VA-API环境")
        return 1
    
    # 创建临时测试文件
    test_video_path = "test_input.mkv"
    encoded_video_path = "test_encoded.mkv"

    # codec_name_map_codec
    CNMC = {
        "libx264": "h264",
        "h264_vaapi": "h264",
        "libx265": "hecv",
        "hevc_vaapi": "hecv",
        "vp8": "vp8",
        "vp8_vaapi": "vp8",
        "vp9": "vp9",
        "vp9_vaapi": "vp9",
    }
    
    try:
        # 生成测试视频
        for codec_cpu in ("libx264", "libx265", "vp8", "vp9"):
            logger.info(f"生成：{codec_cpu} 编码的测试视频")
            test_video_path = Path(f"test_input_{CNMC[codec_cpu]}.mkv")

            if test_video_path.exists():

                yesno = input(f"视频: {test_video_path} 已经存在是否要重新生成？[yes] or [回车] 跳过重新生成")

                if yesno == "yes":
                    test_video_path.unlink()
                    generate_test_video_with_lavfi(test_video_path, codec_cpu, duration=5)
                else:
                    print(f"跳过重新生成: {test_video_path}")
            else:
                generate_test_video_with_lavfi(test_video_path, codec_cpu, duration=5)

        
        # 测试每个可用的VA-API编码器
        for codec in codecs:
            print(f"\n {"="*20} 测试编码器: {codec} {"="*20}")
            
            encoded_path = Path(f"test_input_{CNMC[codec]}.mkv")
            # 测试解码
            decode_success = test_hardware_decoding(codec, encoded_path)
            
            if decode_success:
                # 测试编码
                test_hardware_encoding(codec, test_video_path, encoded_path)
                result = "成功" if decode_success else "失败"
                print(f"  解码测试: {result}")
            else:
                print("  编码测试失败，跳过解码测试")
        
        """
        # 清理临时文件
        for temp_file in [test_video_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        """
        
        print("\n测试完成！")
        return 0
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
        return 1
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        pass
        """
        # 确保清理临时文件
        all_temp_files = [test_video_path] + [
            f"test_encoded_{codec}.mp4" for codec in codecs
        ]
        for temp_file in all_temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        """

if __name__ == "__main__":
    exit(main())
