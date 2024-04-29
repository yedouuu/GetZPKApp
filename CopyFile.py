import win32clipboard
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import re
from ctypes import *
import os
# import logging

# 设置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class DROPFILES(Structure):
    _fields_ = [
        ("pFiles", c_uint),
        ("x", c_long),
        ("y", c_long),
        ("fNC", c_int),
        ("fWide", c_bool),
    ]

pDropFiles = DROPFILES()
pDropFiles.pFiles = sizeof(DROPFILES)
pDropFiles.fWide = True
metadata = bytes(pDropFiles)

def setClipboardFiles(paths):
    if not all(os.path.exists(path) for path in paths):
        # logging.error("One or more files do not exist.")
        print("One or more files do not exist.")
        return

    files = ("\0".join(paths)).replace("/", "\\")
    data = files.encode("U16")[2:] + b"\0\0"
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, metadata + data)
        print("Files copied to clipboard successfully.")
    except Exception as e:
        print(f"Failed to set clipboard data: {e}")
    finally:
        win32clipboard.CloseClipboard()



def copy_to_clipboard(paths):
    """
    :list paths: 文件路径列表
    """
    print(f"Attempting to copy files: {paths}")
    # setClipboardFiles(paths)
    command = f"powershell Set-Clipboard -LiteralPath {paths}"
    os.system(command)

def open_file_path(path):
    """
    :param path: 文件路径
    """

    """
    1. 处理特殊字符：将路径字符串中的单引号替换为两个单引号('')。这是为了确保 PowerShell 
        能够正确解释传递给它的路径字符串，即使路径中包含如单引号这样的特殊字符。
    2. 构造命令：使用 'Start-Process explorer '{safe_path}'' 来启动资源管理器，
        并打开指定路径。这里用单引号 (') 将整个路径围起来，确保 PowerShell 正确处理路径中的特殊字符。
    3. 错误检查：使用 check=True 参数，确保如果命令执行失败，则抛出异常。这有助于及时捕捉错误并进行调试。
    """
    # 安全地处理路径，包含特殊字符
    # 使用单引号围绕路径，并替换内部的单引号以避免中断
    safe_path = path.replace("'", "''")

    # 构造 PowerShell 命令，使用单引号围绕安全路径
    command = ['powershell', '-c', f"Start-Process explorer '{safe_path}'"]

    # 执行命令，并检查错误
    subprocess.run(command, check=True)



def show_message(msg: str):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("提示", msg)
    root.destroy()

def is_valid_filename(filename, remote_folder):
    # 检查非法字符
    if re.search(r'[\\/*?:"<>|]', filename):
        show_message("文件名包含非法字符")
        return False
    
    # 检查文件名长度
    if len(filename) < 1 or len(filename) > 255:
        show_message("文件名长度不符合规定")
        return False

    # 检查文件扩展名
    if not filename.lower().endswith(('.bin')):
        show_message("文件扩展名不合法, 必须为.bin")
        return False

    if not f"ui_resource_{remote_folder}" in filename:
        show_message(f"文件名中必须包含ui_resource_{remote_folder}")
        return False

    # 其他检查可以继续添加
    return True

def select_and_upload_file(destination_path, remote_folder):
    """
    仅仅用于上传UI文件, 文件名称必须包含ui_resource
    :param destination_path: 目标路径
    """
    # 初始化Tkinter，这步是创建文件选择窗口的前提
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 打开文件选择对话框，并获取选择的文件路径
    file_path = filedialog.askopenfilename()
    
    try:
        if file_path:
            file_name = os.path.basename(file_path)
            if is_valid_filename(file_name, remote_folder):
                print(f"Selected file: {file_path}")
                # 调用上传函数
                upload_file(file_path, destination_path)
        else:
            print("No file selected.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        root.destroy()  # 销毁Tkinter窗口

def upload_file(source_path, destination_path):
    # 安全地处理源和目标路径，包含特殊字符
    safe_source = source_path.replace("'", "''")
    safe_destination = destination_path.replace("'", "''")

    # 构造 PowerShell 命令，使用单引号围绕安全路径
    command = [
        'powershell', '-c',
        f"Copy-Item -Path '{safe_source}' -Destination '{safe_destination}'"
    ]

    # 执行命令，并检查错误
    subprocess.run(command, check=True)


if __name__ == '__main__':
    filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\WL_UN60NEW_240409B.93BE741F50EDED2A.ZPK"]
    # filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\README.md"]
    # copy_to_clipboard(filename)
    # open_file_path("D:\\200_WL\\210_GL20双CIS")
    # select_and_upload_file("D:\\200_WL\\210_GL20双CIS")
    # show_message()
