
import tkinter as tk
from tkinter import (
    ttk
)

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.label = tk.Label(self.root, text='这里是检测框', width=4, height=6, bd=5, relief='groove', highlightthickness=2, highlightcolor='red')
        self.label.pack()

if __name__ == '__main__':
    app = App()
    app.root.mainloop()
