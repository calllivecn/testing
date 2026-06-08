import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os
import platform

class ImageRectSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("图片矩形选择工具 (1:1 原图显示)")
        # 设置一个合理的初始窗口大小，大图片通过滚动条查看
        self.root.geometry("1000x800")
        
        # 变量初始化
        self.cv_img = None       # OpenCV 读取的原始图像
        self.img_tk = None       # Tkinter 显示的图像对象
        self.rect_id = None      # Canvas 上的矩形 ID
        
        # 矩形坐标 [x1, y1, x2, y2] (基于原图真实像素)
        self.rect_coords = [0, 0, 0, 0]
        
        # 交互状态
        self.dragging = False
        self.resizing = False
        self.resize_dir = None   
        self.start_x = 0
        self.start_y = 0
        self.margin = 8          # 边缘检测容差(像素)
        
        # 图片真实宽高
        self.img_width = 0
        self.img_height = 0

        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        # 顶部按钮栏
        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="加载图片", command=self.load_image, width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="获取矩形信息", command=self.get_rect_info, width=15).pack(side=tk.LEFT, padx=10)
        tk.Label(btn_frame, text="提示: 图片 1:1 显示，大图片请使用滚动条或鼠标滚轮查看", fg="gray").pack(side=tk.RIGHT, padx=10)
        
        # 主内容框架 (包含画布和滚动条)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        v_scroll = tk.Scrollbar(main_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = tk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 画布 (用于显示图片和绘制矩形)
        self.canvas = tk.Canvas(
            main_frame, bg="#2b2b2b", highlightthickness=0,
            yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        
        # 绑定鼠标滚轮事件 (支持跨平台)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)        # Windows / macOS
        self.canvas.bind("<Button-4>", self.on_mousewheel_linux)    # Linux 向上
        self.canvas.bind("<Button-5>", self.on_mousewheel_linux)    # Linux 向下

    def load_image(self):
        """加载并 1:1 显示图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if not file_path or not os.path.exists(file_path):
            return

        # 1. 使用 OpenCV 读取图片 (不进行任何缩放)
        self.cv_img = cv2.imread(file_path)
        if self.cv_img is None:
            messagebox.showerror("错误", "无法读取图片，请检查文件是否损坏。")
            return

        # 2. 获取真实尺寸
        self.img_height, self.img_width = self.cv_img.shape[:2]

        # 3. 转换颜色空间 (BGR -> RGB) 并编码为 PNG 字节流
        #img_rgb = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        #_, img_encoded = cv2.imencode('.png', img_rgb)
        _, img_encoded = cv2.imencode('.png', self.cv_img)
        
        # 4. 创建 Tkinter PhotoImage
        self.img_tk = tk.PhotoImage(data=img_encoded.tobytes())
        
        # 5. 在 Canvas 上显示图片
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        
        # 6. 配置滚动区域为图片的真实大小 (核心：实现 1:1 显示)
        self.canvas.config(scrollregion=(0, 0, self.img_width, self.img_height))
        
        # 7. 初始化默认矩形 (居中，占图片 1/4 大小，坐标基于原图)
        rect_w = self.img_width // 2
        rect_h = self.img_height // 2
        x1 = (self.img_width - rect_w) // 2
        y1 = (self.img_height - rect_h) // 2
        self.rect_coords = [x1, y1, x1 + rect_w, y1 + rect_h]
        
        # 将视图滚动到矩形所在位置，方便用户查看
        self.canvas.xview_moveto(x1 / self.img_width)
        self.canvas.yview_moveto(y1 / self.img_height)
        
        self.draw_rectangle()

    def draw_rectangle(self):
        """在 Canvas 上绘制矩形"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        x1, y1, x2, y2 = self.rect_coords
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline="#00ff00", width=2, dash=(6, 4)
        )

    def get_resize_dir(self, x, y):
        """判断鼠标是否在矩形边缘，返回调整方向 (x,y 为画布全局坐标)"""
        x1, y1, x2, y2 = self.rect_coords
        m = self.margin
        
        if not (x1 - m <= x <= x2 + m and y1 - m <= y <= y2 + m):
            return None

        left = abs(x - x1) <= m
        right = abs(x - x2) <= m
        top = abs(y - y1) <= m
        bottom = abs(y - y2) <= m

        if top and left: return 'nw'
        if top and right: return 'ne'
        if bottom and left: return 'sw'
        if bottom and right: return 'se'
        if top: return 'n'
        if bottom: return 's'
        if left: return 'w'
        if right: return 'e'
        return None

    def on_press(self, event):
        """鼠标按下"""
        if not self.img_tk: return
        
        # 核心：将屏幕可视区坐标转换为画布全局坐标 (即原图真实像素坐标)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        direction = self.get_resize_dir(x, y)
        if direction:
            self.resizing = True
            self.resize_dir = direction
            self.start_x, self.start_y = x, y
            return

        x1, y1, x2, y2 = self.rect_coords
        if x1 <= x <= x2 and y1 <= y <= y2:
            self.dragging = True
            self.start_x, self.start_y = x, y

    def on_drag(self, event):
        """鼠标拖动"""
        if not (self.dragging or self.resizing): return
        
        # 转换为全局坐标
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        dx = x - self.start_x
        dy = y - self.start_y
        x1, y1, x2, y2 = self.rect_coords

        if self.dragging:
            x1 += dx; y1 += dy; x2 += dx; y2 += dy
        elif self.resizing:
            d = self.resize_dir
            if 'n' in d: y1 += dy
            if 's' in d: y2 += dy
            if 'w' in d: x1 += dx
            if 'e' in d: x2 += dx

        # 限制最小尺寸 (20x20)
        if x2 - x1 < 20:
            if 'w' in (self.resize_dir or ''): x1 = x2 - 20
            else: x2 = x1 + 20
        if y2 - y1 < 20:
            if 'n' in (self.resize_dir or ''): y1 = y2 - 20
            else: y2 = y1 + 20

        # 限制不能超出原图真实边界
        x1 = max(0, min(x1, self.img_width))
        y1 = max(0, min(y1, self.img_height))
        x2 = max(0, min(x2, self.img_width))
        y2 = max(0, min(y2, self.img_height))

        self.rect_coords = [x1, y1, x2, y2]
        self.draw_rectangle()
        
        self.start_x, self.start_y = x, y

    def on_release(self, event):
        """鼠标释放"""
        self.dragging = False
        self.resizing = False
        self.resize_dir = None

    def on_motion(self, event):
        """鼠标移动（更新光标样式）"""
        if not self.img_tk: return
        
        # 转换为全局坐标
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        direction = self.get_resize_dir(x, y)
        
        cursor_map = {
            'n': 'top_side', 's': 'bottom_side',
            'e': 'right_side', 'w': 'left_side',
            'nw': 'top_left_corner', 'ne': 'top_right_corner',
            'sw': 'bottom_left_corner', 'se': 'bottom_right_corner'
        }
        
        if direction:
            self.canvas.config(cursor=cursor_map[direction])
        elif self.rect_coords[0] <= x <= self.rect_coords[2] and self.rect_coords[1] <= y <= self.rect_coords[3]:
            self.canvas.config(cursor="fleur") 
        else:
            self.canvas.config(cursor="")

    def on_mousewheel(self, event):
        """处理 Windows / macOS 的鼠标滚轮事件"""
        if platform.system() == 'Darwin':  # macOS
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:  # Windows
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(self, event):
        """处理 Linux 的鼠标滚轮事件"""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def get_rect_info(self):
        """获取并输出矩形信息 (原图真实像素坐标)"""
        if not self.img_tk:
            messagebox.showwarning("提示", "请先加载图片！")
            return

        x1, y1, x2, y2 = [int(c) for c in self.rect_coords]
        w = x2 - x1
        h = y2 - y1
        
        info = (
            f"【原图真实矩形信息】\n\n"
            f"原图尺寸: {self.img_width} x {self.img_height}\n\n"
            f"左上角坐标 (X, Y): ({x1}, {y1})\n"
            f"右下角坐标 (X, Y): ({x2}, {y2})\n"
            f"宽度 (Width): {w}\n"
            f"高度 (Height): {h}\n\n"
            f"(注: 以上坐标均为 1:1 原图真实像素坐标，可直接用于 OpenCV 裁剪)"
        )
        
        # 在控制台打印
        print("="*40)
        print(f"原图尺寸: {self.img_width} x {self.img_height}")
        print(f"Rect Info: x={x1}, y={y1}, w={w}, h={h}")
        print(f"OpenCV 裁剪代码: img[{y1}:{y1+h}, {x1}:{x1+w}]")
        print("="*40)
        
        # 弹窗显示
        messagebox.showinfo("矩形信息", info)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRectSelector(root)
    root.mainloop()
