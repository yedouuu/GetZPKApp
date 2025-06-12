import tkinter as tk
import subprocess
import re
from ctypes import *
import os
from tkinter import (
    filedialog, 
    messagebox, 
)
import shutil
import xml_Utils
from file_Utils import copy_to_clipboard
# import logging

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
    abs_path = os.path.abspath(path)
    safe_path = abs_path.replace("'", "''")

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


def create_empty_rootfs():
    """ 从空白模板创建 rootfs 
        return : rootfs_path
        Ex: ./1_WLGL18_240411/rootfs/rootfs_20011b
    """
    rootfs_template_path = xml_Utils.get_text("local_template_rootfs_path")
    rootfs_path = xml_Utils.get_text("local_rootfs_path")
    if not os.path.exists(rootfs_template_path):
        xml_Utils.print_red_text(f"rootfs_template_path:{rootfs_template_path} not exists")
        return None
    
    if os.path.exists(rootfs_path):
        try:
            shutil.rmtree(rootfs_path)
            print(f"Existing rootfs_path '{rootfs_path}' has been removed.")
        except Exception as e:
            xml_Utils.print_red_text(f"Failed to remove existing rootfs_path '{rootfs_path}': {e}")
            return None


    shutil.copytree(rootfs_template_path, rootfs_path)
    if not os.path.exists(rootfs_path):
        xml_Utils.print_red_text(f"rootfs_path:{rootfs_path} create failed")
        return None
    return rootfs_path

def copy_files_to_rootfs(src, dst):
    """Copy currency-specific files from source to destination rootfs.
    
    Args:
        src: Source rootfs path
        dst: Destination rootfs path
    """
    if not all(os.path.exists(path) for path in [src, dst]):
        xml_Utils.print_red_text("【Error】Source or destination path not found")
        return None

    # Get currency codes to copy
    currency_codes = set(xml_Utils.get_open_country("UN60D")) - {"AUT", "MIX", "USD"}
    print(f"【Info】Copying files for currencies: {currency_codes}")

    # Define directory mappings and their copy modes
    DIRS = {
        "CashTemplate_COLOR": "file",
        "CashTemplate_NEW": "dir",
        "IMG_AUTO": "file"
    }

    def copy_item(src_path, dst_path, copy_mode="file"):
        """Copy a single file or directory if it matches the currency code"""
        try:
            if copy_mode == "file":
                shutil.copy2(src_path, dst_path)
            else:
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            print(f"【Info】Copied: {os.path.basename(src_path)}")
            return True
        except Exception as e:
            print(f"【Error】Failed to copy {src_path}: {e}")
            return False

    # Process template files and counterfiet xml files
    for dirname, copy_mode in DIRS.items():
        src_dir = os.path.join(src, dirname)
        dst_dir = os.path.join(dst, dirname)
        
        if not os.path.exists(src_dir):
            print(f"【Warning】Source directory not found: {src_dir}")
            continue

        os.makedirs(dst_dir, exist_ok=True)
        
        for item in os.listdir(src_dir):
            if any(code in item for code in currency_codes):
                src_item = os.path.join(src_dir, item)
                dst_item = os.path.join(dst_dir, item)
                copy_item(src_item, dst_item, copy_mode)

    """ Process currecnys.xml, user_config.xml """
    # src_dir = xml_Utils.get_text("local_currencys_xml_path")
    
    # src_dir = xml_Utils.get_text("local_main_rootfs_path")
    # src_dir = os.path.join(xml_Utils.get_text("local_main_rootfs_path"), "IMG_AUTO")

    dst_dir = xml_Utils.get_text("local_rootfs_path")
    dst_dir = os.path.join(dst_dir, "IMG_AUTO")

    FILES = {
        "currencys.xml": {
            "type":"file", 
            "src_dir":xml_Utils.get_text("local_currencys_xml_path"), 
            "dst_dir":dst_dir
        },
        "user_config.xml": {
            "type":"file", 
            "src_dir":os.path.join(xml_Utils.get_text("local_main_rootfs_path"), "IMG_AUTO"), 
            "dst_dir":dst_dir
        },
    }

    for item in os.listdir(src_dir):
        if item in FILES.keys():
            src_dir = os.path.join(FILES[item]["src_dir"], item)
            dst_dir = os.path.join(FILES[item]["dst_dir"], item)
            copy_item(src_dir, dst_dir, FILES[item]["type"])
 
def GL18_modify_user_config(src, dst):
    """ GL18修改user_config中自定义内容 
        Arg:
            src: str, 源文件路径
            dst: str, 目标文件路径
    """
    src_root = xml_Utils.LXML_ET.parse(src).getroot()
    dst_tree = xml_Utils.LXML_ET.parse(dst)

    for child in src_root.findall("item"):
        for key, val in child.attrib.items():
            # print(key, val)
            if key == 'name':
                print(f"{key} = {val}")
                el_list = dst_tree.xpath(f'/item[@name="{val}"]')
                if el_list:
                    element = el_list[0]
                else:
                    break    
            else: 
                element.set(key, val)  # 修改value属性
                print(f"Set {key} = {val}")
    # 保存修改到文件
    dst_tree.write(dst, encoding='utf-8', pretty_print=True)

def GL18_modify_ZPK_version(new_file_name, dst):
    dst_tree = xml_Utils.LXML_ET.parse(dst)
    element = dst_tree.xpath('/config/item[@name="ZpkVersion"]')[0]
    print(f"【Info】ZpkVersion = {element.get('value')}")
    element.set('value', new_file_name)
    print(f"【Info】Set ZpkVersion = {new_file_name}")
    # 保存修改到文件
    dst_tree.write(dst, encoding='utf-8', pretty_print=True)
    

def create_rootfs_image(bat_path: str = "") -> bool:
    """Create rootfs image using specified bat file
    
    Args:
        bat_path: Path to the bat file, if empty will use default from config
    Returns:
        bool: True if successful, False otherwise
    """
    if not bat_path:
        bat_path = xml_Utils.get_text("local_create_rootfs_image_bat_path")
    
    # Validate bat file exists
    if not os.path.exists(bat_path):
        xml_Utils.print_red_text(f"bat_path: {bat_path} not exists")
        return False

    try:
        # Convert to absolute path and normalize slashes
        abs_bat_path = os.path.abspath(bat_path)
        
        # Run bat file from its directory
        bat_dir = os.path.dirname(abs_bat_path)
        bat_name = os.path.basename(abs_bat_path)
        
        # Change to bat directory and execute
        current_dir = os.getcwd()
        os.chdir(bat_dir)
        
        result = subprocess.run(
            f"cmd /c {bat_name}", 
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Print output for debugging
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        return True

    except subprocess.CalledProcessError as e:
        xml_Utils.print_red_text(f"Failed to run bat file: {e}")
        if e.output:
            print(f"Error output: {e.output}")
        return False
        
    finally:
        # Restore original working directory
        os.chdir(current_dir)

def GL18_create_rootfs_image(new_file_name:str, customer_code: str = ""):
    """ 创建 GL18 rootfs """

    src = xml_Utils.get_text("local_main_rootfs_path")
    dst = create_empty_rootfs()
    copy_files_to_rootfs(src, dst)

    user_config_src = "./user_config.xml"
    user_config_dst = os.path.join(dst, "IMG_AUTO", "user_config.xml")
    GL18_modify_user_config(user_config_src, user_config_dst)
    GL18_modify_ZPK_version(new_file_name, user_config_dst)

    create_rootfs_image_path = xml_Utils.get_text("local_create_rootfs_image_bat_path")
    rootfs_image_path = dst + ".bin"
    print(f"【Info】create_rootfs_image_path:{create_rootfs_image_path}")
    print(f"【Info】rootfs_image_path:{rootfs_image_path}")

    create_rootfs_image(create_rootfs_image_path)

    return rootfs_image_path


if __name__ == '__main__':
    filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\WL_UN60NEW_240409B.93BE741F50EDED2A.ZPK"]
    # filename = [r"D:\004_laboratory\GetZPK\ZPK\88.001288_以色列\README.md"]
    # copy_to_clipboard(filename)
    # open_file_path("D:\\200_WL\\210_GL20双CIS")
    # select_and_upload_file("D:\\200_WL\\210_GL20双CIS")
    # show_message()

    file_system = GL18_create_rootfs_image("WL_UN60DENRU_250425B")
    print(f"file system = {file_system}")
