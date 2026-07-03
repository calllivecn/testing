import gi

# 1. 严格指定 GTK4 版本（必须在导入前调用）
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

def get_desktop_scale_factor():
    """安全获取当前显示器的缩放比例（GTK4 专用）"""
    # 2. 关键：创建临时 Gtk.Application 触发初始化
    app = Gtk.Application(application_id="com.example.scalecheck")
    app.register()
    
    # 3. 此时可安全获取 display（不再为 None）
    display = Gdk.Display.get_default()
    if not display:
        raise RuntimeError("无法获取显示设备：请在图形会话中运行此脚本")
    
    # 4. 获取主显示器的缩放比例
    monitor = display.get_primary_monitor()
    if not monitor:
        monitors = display.get_monitors()
        if monitors.get_n_items() == 0:
            raise RuntimeError("未检测到显示器")
        monitor = monitors.get_item(0)
    
    return monitor.get_scale_factor()

if __name__ == "__main__":
    try:
        scale = get_desktop_scale_factor()
        print(f"当前显示器缩放比例: {scale}x")
        # 示例：物理像素 → 逻辑坐标转换
        physical_width = 1920
        logical_width = physical_width / scale
        print(f"物理宽度 {physical_width}px = 逻辑坐标 {logical_width:.1f} 单位")
    except Exception as e:
        print(f"错误: {str(e)}")
