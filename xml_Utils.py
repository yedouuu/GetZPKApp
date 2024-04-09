import paramiko
import datetime
import os
from os import system
import xml.etree.ElementTree as ET
import lxml.etree as LXML_ET
from colorama import Fore, Style, init
from tqdm import tqdm
import time
import asyncio

def print_red_text(text):
    print(Fore.RED + text + Style.RESET_ALL)

def print_green_text(text):
    print(Fore.GREEN + text + Style.RESET_ALL)

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

def get_text(tag, type="one"):
    """ 查找指定tag的text值
	one:(默认值)返回一个元素的text
	all:以List返回所有查找到的元素的text
    """
    try:
        if type == "one":
            return config_tree.find(tag).text
        elif type == "all":
            return [ dir.text for dir in config_tree.findall(tag)]
    except AttributeError as e:
        print_red_text(f"【ERROR】文件读取错误：{e}")
        print_red_text(f"【ERROR】文件读取错误：{tag}")
        input("按任意键退出...")
        exit()

def path_valide(path):
    """ 检查路径是否有效 """
    if not path.endswith('/'):
        path += '/'
    return path

config_tree = open_xml('./ssh_config.xml')
local_currencys_xml_path = path_valide(get_text("local_currencys_xml_path"))
currency_tree = open_xml(local_currencys_xml_path + "currencys.xml")

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




def get_ui_file_time(filename):
    file_path = get_text("local_ui_file_path") + filename
    file_mtime = os.path.getmtime(file_path)
    mtime = time.localtime(file_mtime)
    return time.strftime("%Y-%m-%d %H:%M", mtime)
    # print("文件的最后一修改时间（可读格式）：", time.strftime("%Y-%m-%d %H:%M:%S", mtime))


def map_ui_file_name(remote_directory):
    """ 
    输入：
    1. UN60_OLD
    2. UN70_NEW
    3. UN200_TOUCH
    4. UN60_XXX
    根据选择的remote_directory, 返回对应的ui_resource_xxx.bin文件名称
    1. UN60_OLD      --> ui_resource_UN60_OLD.bin
    2. UN70_NEW      --> ui_resource_UN70_NEW.bin
    3. UN200_TOUCH    --> ui_resource_UN200_TOUCH.bin
    4. UN60_XXX      --> ui_resource_UN60_XXX.bin
    return ui_resource_XXX
    """

    # /home/lin/Desktop/UN60_OLD/ -> UN60_OLD
    directory_ver = remote_directory
    ui_file_name = "ui_resource_"

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
    current_folder = get_text("local_ui_file_path")
    contents = os.listdir(current_folder)
    ui_file_name = map_ui_file_name(remote_directory)
    ret = [content for content in contents if '.bin' in content and f"{ui_file_name}" in content]
    return ret

def get_remote_directorys():
	return get_text("remote_directory", "all")

def get_remote_directory_version(remote_directory, type="ver"):
    """ 获取远端目录版本

    return:
    type = "ver"
    1. /home/lin/Desktop/UN60_OLD/    -> OLD
    2. /home/lin/Desktop/UN60_NEW/    -> NEW
    3. /home/lin/Desktop/UN60_TOUCH/  -> TOUCH
    
    type = "full"
    1. /home/lin/Desktop/UN60_OLD/    -> UN60_OLD
    2. /home/lin/Desktop/UN200_NEW/    -> UN200_NEW
    """
    directory_name = remote_directory.split('/')[-2]
    if "full" in type:
        return directory_name.upper()
    elif "ver" in type:
        return directory_name.split('_')[-1].upper()

def get_open_country():
    """ 获取开启的国家 """
    country_code = []
    for e in currency_tree.iter("Country"):
        tmp = e.find("selecttion").get("val")
        if tmp == "Y":
            country_code.append(e.get("tag"))
    return country_code

async def ssh_connect():
        """ 连接服务器 """
        # SSH 连接参数
        hostname = get_text('hostname')
        username = get_text('username')
        port = get_text('port')
        password = get_text('password')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=port, username=username, password=password)
        sftp = ssh.open_sftp()
        return ssh, sftp

class SSH_Client():
    ssh = None
    sftp = None
    ssh_client = None
    def __init__(self):
        pass
    
    async def connect(self):
        self.ssh, self.sftp = await ssh_connect()

    def get_ssh(self):
        return self.ssh

    def get_sftp(self):
        return self.sftp
    
    def close(self):
        self.ssh.close()
        self.sftp.close()

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
    
    return new_ver


def get_download_zpk_path(remote_directory:str):
    """ 获取下载ZPK的路径 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    directory_ver = directory_ver.replace("_", "")

    """ 6.2 在当前创建对应目录版本的文件夹 """
    local_zpk_path = path_valide(get_text('local_zpk_path'))
    # ./UN60NEW/
    download_zpk_path = path_valide(local_zpk_path + directory_ver)
    if not os.path.exists(download_zpk_path):
        os.makedirs(download_zpk_path)

    return download_zpk_path


def generate_new_name(remote_directory:str):
    """ 获取最新的版本名字 """

    """ 6.1 获取ZPK版本 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    directory_ver = directory_ver.replace("_", "")

    download_zpk_path = get_download_zpk_path(remote_directory)

    """ 生成新的文件名 """
    current_date = datetime.date.today().strftime("%y%m%d")
    ver = get_version(download_zpk_path, current_date)

    file_name = f'WL_{directory_ver}_{current_date}' + ver

    return file_name



async def modify_user_config(ssh_client:SSH_Client, remote_directory:str):
    """ 修改user_config文件为最新的版本号 """
    sftp = ssh_client.get_sftp()
    file_name = generate_new_name(remote_directory)

    user_config_xml_path = get_text('remote_user_config_xml_path')
    user_config_xml = sftp.open(remote_directory + user_config_xml_path, 'r')
    try:
        user_config_tree = LXML_ET.parse(user_config_xml)
        # 在这里可以继续处理已解析的XML数据
    except LXML_ET.ParseError as e:
        print(f"XML解析错误：{e}")
        input("按任意键退出...")
        exit()
    except IOError as e:
        print(f"文件读取错误：{e}")
        input("按任意键退出...")
        exit()

    element = user_config_tree.xpath('/config/item[@name="ZpkVersion"]')[0]  # 获取元素2
    element.set('value', file_name)  # 修改value属性
    # 调整缩进
    LXML_ET.indent(user_config_tree, space="\t", level=0)
    # 您可以将修改后的tree写入文件，例如：
    modified_xml = LXML_ET.tostring(user_config_tree.getroot(), encoding="utf-8", xml_declaration=True)
    sftp.file(remote_directory + user_config_xml_path, 'w').write(modified_xml)


async def upload_currencys_xml(ssh_client:SSH_Client ,remote_directory:str):
    """ 上传货币配置文件 """
    try:
        sftp = ssh_client.get_sftp()
        remote_currencys_xml_path = get_text('remote_currencys_xml_path')
        sftp.put(local_currencys_xml_path+'currencys.xml', remote_directory+remote_currencys_xml_path+'currencys.xml')
    except Exception as e:
        print(f"【Error】上传货币配置文件失败：{e}")

async def upload_ui_file(ssh_client:SSH_Client ,remote_directory:str, ui_file:str):
    """ 上传ui文件 """
    try:
        sftp = ssh_client.get_sftp()

        remote_ui_file_name = get_text('remote_ui_file_name')
        if not remote_ui_file_name.endswith('.bin'):
            remote_ui_file_name += '.bin'

        local_ui_file_path = get_text('local_ui_file_path')
        remote_ui_file_path = get_text('remote_ui_file_path')

        print(f"【Info】上传{ui_file} -> {remote_ui_file_name}")
        sftp.put(local_ui_file_path+ui_file, remote_directory+remote_ui_file_path+remote_ui_file_name)
    except Exception as e:
        print(f"【Error】上传{ui_file}失败：{e}")



async def pack_and_down_zpk(ssh_client:SSH_Client ,remote_directory:str, ui_file:str):
    """ 打包zpk文件 """
    ssh = ssh_client.get_ssh()
    sftp = ssh_client.get_sftp()
    
    await modify_user_config(ssh_client, remote_directory)

    cmd_get_file_amount = f'cd {remote_directory}/upgrade; find . | wc -l'
    stdin, stdout, stderr = ssh.exec_command(cmd_get_file_amount)
    file_count = int(stdout.read().strip())

    sftp.chdir(remote_directory)
    get_latest_file = "ls -lt | head -n 2 | tail -n 1 | awk '{print $9}'"
    remote_run_script = get_text('remote_run_script')
    
    file_name = generate_new_name(remote_directory)
    command = f"cd {remote_directory}; sh {remote_run_script} {file_name}"
    
    # 打开一个SSH的channel
    channel = ssh.get_transport().open_session()
    channel.get_pty()
    channel.exec_command(command)

    """ 9. 等待脚本执行完成, 获取ZPK """
    if channel.recv_exit_status() != 0:
        # 脚本执行失败时的错误处理
        print("【Error】: Remote command execution failed.")
        print(stderr.read().decode())
    else:
        """ 下载ZPK文件 """
        download_zpk_path = get_download_zpk_path(remote_directory)
        stdin, stdout, stderr = ssh.exec_command('cd ' + remote_directory + '; ' + get_latest_file)
        latest_file = stdout.read().decode().strip()
        local_file_path = download_zpk_path + latest_file
        remote_file_path = remote_directory + latest_file
        sftp.get(remote_file_path, local_file_path)
