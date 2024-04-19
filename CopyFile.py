import win32clipboard
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

pDropFiles = DROPFILES()
pDropFiles.pFiles = sizeof(DROPFILES)
pDropFiles.fWide = True
metadata = bytes(pDropFiles)

def copy_to_clipboard(paths):
    """
    :list paths: 文件路径列表
    """
    print(f"Attempting to copy files: {paths}")
    setClipboardFiles(paths)

if __name__ == '__main__':
    filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\WL_UN60NEW_240409B.93BE741F50EDED2A.ZPK"]
    # filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\README.md"]
    copy_to_clipboard(filename)