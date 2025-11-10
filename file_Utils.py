import os

import pyperclip

def copy_to_clipboard(paths):
    """
    :list paths: 文件路径列表
    """
    print(f"Attempting to copy files: {paths}")
    # setClipboardFiles(paths)
    command = f"powershell Set-Clipboard -LiteralPath {paths}"
    os.system(command)
    
def copy_text_to_clipboard(text: str):
    """复制文本到剪贴板"""
    try:
        pyperclip.copy(text)
        print(f"已复制到剪贴板: {text}")
    except Exception as e:
        print(f"复制失败: {e}")