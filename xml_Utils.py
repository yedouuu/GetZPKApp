import paramiko
import datetime
import os
from os import system
import xml.etree.ElementTree as ET
import lxml.etree as LXML_ET
from colorama import Fore, Style, init
from tqdm import tqdm
import time

def open_xml(filename):
    try:
        tree = ET.parse(filename)
        # 在这里可以继续处理已解析的XML数据
        return tree
    except ET.ParseError as e:
        print_red_text(f"XML解析错误：{e}")
        input("按任意键退出...")
        exit()
    except IOError as e:
        print_red_text(f"文件读取错误：{e}")
        input("按任意键退出...")
        exit()

config_tree = open_xml('./ssh_config.xml')

def get_version(current_folder, current_date):
    new_ver = 'A'
    
    contents = os.listdir(current_folder)  # Get the list of contents
    if len(contents) == 0:
        return new_ver
    # 获取当前文件夹下的所有文件
    s = [content.split('.')[0][-1] for content in contents if 'ZPK' in content and f"{current_date}" in content]
    if len(s) > 0:
        max_s = max(s)
        new_ver = chr((ord(max_s) - ord('A') + 1) % 26 + ord('A'))


def get_text(tag, type="one"):
    """ 查找指定tag的text值
	one:(默认值)返回一个元素的text
	all:以List返回所有查找到的元素的text
    """
    try:
    	if type == "one":
        	return config_tree.find(tag).text
        elif type == "all"
        	return [ dir.text for dir in config_tree.findall(tag)]
    except AttributeError as e:
        print_red_text(f"【ERROR】文件读取错误：{e}")
        print_red_text(f"【ERROR】文件读取错误：{tag}")
        input("按任意键退出...")
        exit()


def map_ui_file_name(remote_directory):
    """ 
    输入：
    1. /home/lin/Desktop/UN60_OLD/
    2. /home/lin/Desktop/UN60_NEW/
    3. /home/lin/Desktop/UN60_TOUCH/
    4. /home/lin/Desktop/UN60_DEV/
    根据选择的remote_directory, 返回对应的ui_resource_xxx.bin文件名称
    1. UN60_OLD      --> ui_resource_FTFV.bin
    2. UN60_NEW      --> ui_resource_WLGL20.bin
    3. UN60_TOUCH    --> ui_resource_TOUCH.bin
    4. UN60_XXX      --> ui_resource_XXX.bin
    return ui_resource_XXX
    """

    # /home/lin/Desktop/UN60_OLD/ -> UN60_OLD
    directory_ver = get_remote_directory_version(remote_directory, "full")
    ui_file_name = "ui_resource_"

    if ("OLD" in directory_ver) and ("UN60" in directory_ver):
        ui_file_name += "FTFV"        
    elif ("NEW" in directory_ver) and ("UN60" in directory_ver):
        ui_file_name += "WLGL20"
    else:
        ui_file_name += directory_ver
    return ui_file_name


def scan_ui_files(remote_directory):
    """ 
    根据选择的remote_directory, 返回所有ui_resource_xxx.bin文件 
    1. UN60_NEW      --> ui_resource_WLGL20.bin
    2. UN60_XXX      --> ui_resource_UN60_XXX.bin
    3. UN200_XXX    --> ui_resource_UN200_XXX.bin
    """
    # 获取当前文件夹下的所有文件
    current_folder = config_tree.get_text("local_ui_file_path")
    contents = os.listdir(current_folder)
    ui_file_name = map_ui_file_name(remote_directory)
    ret = [content for content in contents if '.bin' in content and f"{ui_file_name}" in content]
    return ret

def get_remote_directorys():
	dir_list = config_tree.get_text("remote_directory", "all")

def get_remote_directory_version(remote_directory, type="ver"):
    """ 获取远端目录版本 
    type: "full" 返回完整文件名；"ver" 返回版本号
    return 
    ver
    1. /home/lin/Desktop/UN60_OLD/    -> OLD
    2. /home/lin/Desktop/UN60_NEW/    -> NEW
    3. /home/lin/Desktop/UN60_TOUCH/  -> TOUCH
    
    full
    1. /home/lin/Desktop/UN60_OLD/    -> UN60_OLD
    2. /home/lin/Desktop/UN200_NEW/    -> UN200_NEW
    """
    directory_name = remote_directory.split('/')[-2]
    if "full" in type:
        return directory_name.upper()
    elif "ver" in type:
        return directory_name.split('_')[-1].upper()

def get_open_country(config_tree=None):
    """ 获取开启的国家 """
    country_code = []
    for e in config_tree.iter("Country"):
        tmp = e.find("selecttion").get("val")
        if tmp == "Y":
            country_code.append(e.get("tag"))
    return country_code


def path_valide(path):
    """ 检查路径是否有效 """
    if not path.endswith('/'):
        path += '/'
    return path

