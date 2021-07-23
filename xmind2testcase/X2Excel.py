#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import json
import os
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter import filedialog
from tkinter import messagebox
import xmind2testcase.utils as xcase
import platform

# def Main():2


def selectFile():
    path_ = filedialog.askopenfilename()
    path1.set(path_)


def printValue():
    print(value.get())
    print(path1.get())


def operate():

    print(platform.system())
    if path1.get() is None or path1.get() == " ":
        messagebox.showwarning(title="提醒",message="请选择正确的文件路径")
    elif value.get() == 0:
        messagebox.showwarning(title="提醒",message="请选择一个功能")
    else:
        file_path = ""
        file_path = xcase.export_to_excel(path1.get(), value.get())
        os.startfile(file_path)
        # if platform.system() == 'Darwin':
        #     # mac 系统
        #     os.popen("open " + file_path)
        #     # print(file_path)
        # else:
        #     # window 系统
        #     os.startfile(file_path)


if __name__ == '__main__':
    root = Tk()  # 创建窗口对象的背景色
    # 设置标题
    root.title('xmind to excel')
    # 设置window宽高
    root.geometry('600x150')

    path1 = StringVar()
    path2 = StringVar()
    path3 = StringVar()
    # 选择文件
    Label(root, text="").grid(row=0, column=0)
    Label(root, text="选择需要解析的XMind文件:").grid(row=1, column=0, padx=5, pady=5)
    e1 = Entry(root, textvariable=path1)
    e1.grid(row=1, column=1, padx=5, pady=5)
    Button(root, text="选择文件", command=selectFile).grid(row=1, column=2)
    # 选择功能

    value = IntVar()
    value.set(0)

    # Label(root,text="选择需要的功能").grid(row=2, column=0, padx=0, pady=0)
    Radiobutton(root, text="转换成Excel", variable=value, value=1).grid(row=4, sticky=W)
    Radiobutton(root, text="提取P0用例", variable=value, value=2).grid(row=5, sticky=W)
    Button(root, text="转换", command=operate).grid(row=6, sticky=W, padx=5, pady=5)
    selection = value.get()
    print("Selection:", selection)

    root.mainloop()
