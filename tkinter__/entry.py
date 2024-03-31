#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-17 22:50:35
# author calllivecn <calllivecn@outlook.com>

from tkinter import *

root = Tk()

def validate_input(new_value):
    if new_value.isnumeric() or new_value == "":
        if len(new_value) <= 4:
            return True
        else:
            return False
    else:
        return False

validate_cmd = root.register(validate_input)

entry = Entry(root, validate="key", validatecommand=(validate_cmd, '%P'))
entry.insert(0, "1234")
entry.pack()

btn = Button(root, text="查看输入值")
btn.bind("<Button-1>", lambda e: print(entry.get()))
btn.pack()

root.mainloop()

