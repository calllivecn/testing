import tkinter as tk
from tkinter import font, ttk

root = tk.Tk()
root.title("系统可用字体")

style = ttk.Style()
# 修改所有ttk控件的默认字体
style.configure(".", font=("微软雅黑", 12))
# 或者只修改某一类控件，如标签：
# style.configure("TLabel", font=("微软雅黑", 12))


# 获取字体列表（包含 root 后才能调用）
fonts = sorted(font.families())

# 创建滚动条和列表框
scrollbar = ttk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = tk.Listbox(root, yscrollcommand=scrollbar.set, width=60, height=30)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=listbox.yview)

# 插入字体，并用字体本身展示
for i, f in enumerate(fonts):
    listbox.insert(tk.END, f"{i+1}. {f}")
    # 设置每行的字体为该字体（前几个可能因缺字显示异常，但不影响效果）
    try:
        listbox.itemconfig(tk.END, font=(f, 12))
    except:
        pass  # 极少数字体可能无法应用在列表中，忽略即可

root.mainloop()
