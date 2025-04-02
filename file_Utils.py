import os

def copy_to_clipboard(paths):
    """
    :list paths: 文件路径列表
    """
    print(f"Attempting to copy files: {paths}")
    # setClipboardFiles(paths)
    command = f"powershell Set-Clipboard -LiteralPath {paths}"
    os.system(command)