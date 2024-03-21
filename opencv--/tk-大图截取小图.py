



import tkinter as tk
import cv2
import numpy as np

class ImageCropper(tk.Tk):
    def __init__(self, image_path):
        super().__init__()
        self.title('Image Cropper')

        self.original_image = cv2.imread(image_path)
        self.current_image = self.original_image.copy()
        self.displayed_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        self.resized_image = cv2.resize(self.displayed_image, (800, 600), interpolation=cv2.INTER_AREA)
        self.photo_image = tk.PhotoImage(image=np.array(self.resized_image).astype(np.uint8))

        self.canvas = tk.Canvas(self, width=self.resized_image.shape[1], height=self.resized_image.shape[0])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo_image)
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<Key>', self.on_key_press)

        self.crop_rectangle_id = None
        self.crop_start_pos = None
        self.cursor_offset = [0, 0]

    def on_mouse_down(self, event):
        self.crop_start_pos = (event.x, event.y)
        self.cursor_offset = [0, 0]
        self.crop_rectangle_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                              outline="red", dash=(4, 4))

    def on_mouse_drag(self, event):
        if self.crop_start_pos:
            x1, y1 = self.crop_start_pos
            x2, y2 = event.x + self.cursor_offset[0], event.y + self.cursor_offset[1]
            self.canvas.coords(self.crop_rectangle_id, x1, y1, x2, y2)

    def on_key_press(self, event):
        if event.char in ['Up', 'Down', 'Left', 'Right'] and self.crop_rectangle_id:
            dx, dy = {'Up': (-5, 0), 'Down': (5, 0), 'Left': (0, -5), 'Right': (0, 5)}[event.char]
            coords = self.canvas.coords(self.crop_rectangle_id)
            self.cursor_offset[0] += dx
            self.cursor_offset[1] += dy
            self.canvas.coords(self.crop_rectangle_id, coords[0], coords[1], coords[2]+dx, coords[3]+dy)

    def crop_and_save(self):
        """模拟裁剪并保存，此处实际裁剪原始大图并保存"""
        if self.crop_rectangle_id:
            crop_box = self.canvas.bbox(self.crop_rectangle_id)
            # 转换坐标系以匹配OpenCV格式（左上角坐标、宽度、高度）
            x, y, x2, y2 = crop_box
            crop_region = (x, y, x2-x, y2-y)
            cropped_image = self.original_image[crop_region[1]:crop_region[1]+crop_region[3],
                                               crop_region[0]:crop_region[0]+crop_region[2]]
            cv2.imwrite('cropped_image.jpg', cropped_image)

    def run(self):
        self.mainloop()

def main():
    test_image_path = "path_to_your_large_image.jpg"  # 替换为您的大图路径
    cropper = ImageCropper(test_image_path)
    cropper.protocol("WM_DELETE_WINDOW", cropper.quit)  # 在窗口关闭时调用quit函数
    cropper.bind('<Escape>', cropper.destroy)  # 按Esc键关闭窗口
    cropper.run()

if __name__ == "__main__":
    main()