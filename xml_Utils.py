import datetime
import os
import xml.etree.ElementTree as ET
import lxml.etree as LXML_ET
from colorama import Fore, Style, init
import time
from SSHClient import SSH_Client
from CopyFile import copy_to_clipboard

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

def save_xml(tree, filename):
    try:
        ET.ElementTree(tree).write(filename, encoding="utf-8", xml_declaration=True)
    except IOError as e:
        print_red_text(f"文件写入错误：{e}")
        input("按任意键退出...")
        exit()


# ssh_config_tree = open_xml('./ssh_config.xml')
# remote_config_tree = open_xml('./remote_config.xml')
# def get_text(tag, type="one", param=None, config_tree=ssh_config_tree):
#     """ 查找指定tag的text值
# 	one:(默认值)返回一个元素的text
# 	all:以List返回所有查找到的元素的text
#     """
#     try:
#         if type == "one":
#             return config_tree.find(tag).text
#         elif type == "all":
#             return [ dir.text for dir in config_tree.findall(tag)]
#     except AttributeError as e:
#         print_red_text(f"【ERROR】文件读取错误：{e}")
#         print_red_text(f"【ERROR】文件读取错误：{tag}")
#         input("按任意键退出...")
#         exit()


ssh_config_tree = open_xml('./ssh_config.xml')
ssh_config_root = ssh_config_tree.getroot()

remote_config_tree = open_xml('./remote_config.xml')
remote_config_root = remote_config_tree.getroot()

def get_server():
    """ 获取对应服务器上的配置信息 """
    try:
        hostname = ssh_config_root.find("hostname").text
        xpath = f"./Server[@hostname='{hostname}']"
        server = remote_config_root.find(xpath)
        return server
    except AttributeError as e:
        print_red_text(f"【ERROR】文件读取错误：{e}")
        print_red_text(f"【ERROR】Reading Tag：Server")
        input("按任意键退出...")
        exit()


def get_text(tag, type="one", scheme=None, config_tree="ssh_config"):
    """ 查找指定tag的text值

    tag: 要查找的标签

    type:
        - one: (默认值)返回一个元素的text
        - all: 以List返回所有查找到的元素的text

    scheme: 对应的设计方案, 如: GL20, A33

    config_tree: 指定要查找的xml文件, 默认ssh_config.xml
    """
    
    """ ssh_config中查找连接参数 """
    if "ssh_config" in config_tree:
        try:
            if type == "one":
                return ssh_config_tree.find(tag).text
            elif type == "all":
                return [ dir.text for dir in ssh_config_tree.findall(tag)]
        except AttributeError as e:
            print_red_text(f"【ERROR】文件读取错误：{e}")
            print_red_text(f"【ERROR】文件读取错误：{tag}")
            input("按任意键退出...")
            exit()

    elif "remote_config" in config_tree:
        try:
            """ 区分对应的服务器, 获取对应服务器上的目录 """
            if "remote_directory" in tag:
                server = get_server()
                return [dir.text for dir in server.findall(tag)]
            
            if scheme is not None:
                xpath_expr = f"./IMG_DesignScheme[@val='{scheme}']"
                scheme_node = remote_config_root.find(xpath_expr)
                #print(scheme_node)
                return scheme_node.find(tag).text
            
            else:
                print_red_text(f"【ERROR】请输入设计方案")
                input("按任意键退出...")

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


local_currencys_xml_path = path_valide(get_text("local_currencys_xml_path"))
# currency_tree = open_xml(local_currencys_xml_path + "currencys.xml")


def get_ui_file_time(filename):
    file_path = get_text("local_ui_file_path") + filename
    file_mtime = os.path.getmtime(file_path)
    mtime = time.localtime(file_mtime)
    return time.strftime("%Y-%m-%d", mtime)
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
	return get_text("remote_directory", "all", config_tree="remote_config")

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

def get_open_country(remote_folder:str):
    """ 获取开启的国家 """
    # currency_path = get_currency_by_folder(remote_folder)
    path = get_text("local_currencys_xml_path")
    currency_tree = open_xml(path + "currencys.xml")
    country_code = []
    for e in currency_tree.iter("Country"):
        tmp = e.find("selecttion").get("val")
        if tmp == "Y":
            country_code.append(e.get("tag"))
    return country_code

def get_ssh_config():
    """ 获取ssh配置 
    return hostname, username, port, password
    """
    hostname = get_text('hostname')
    username = get_text('username')
    port = get_text('port')
    password = get_text('password')
    key_path = get_text('key_path')
    return {'hostname':hostname,    \
            'port':port,            \
            'username':username,    \
            'password':password,    \
            'key_path':key_path
        }


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

def get_scheme(remote_folder:str):
    """ 获取远端目录的方案 """
    server = get_server()
    for _remote_folder in server.findall("remote_directory"):
        if remote_folder in _remote_folder.text:
            print(_remote_folder.text, "   ", _remote_folder.attrib["IMGDesignScheme"])
            return _remote_folder.attrib["IMGDesignScheme"]
    return None


def get_download_zpk_path(remote_directory:str):
    """ 获取默认下载ZPK的路径 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    directory_ver = directory_ver.replace("_", "")

    """ 6.2 在当前创建对应目录版本的文件夹 """
    local_zpk_path = path_valide(get_text('local_zpk_path'))
    # ./UN60NEW/
    download_zpk_path = path_valide(local_zpk_path + directory_ver)
    if not os.path.exists(download_zpk_path):
        os.makedirs(download_zpk_path)

    return download_zpk_path


def generate_new_name(remote_directory:str, customer_path:str=""):
    """ 获取最新的文件名字 
    return: f'WL_{directory_ver}_{current_date}' + ver
    """

    """ 6.1 获取ZPK版本 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    directory_ver = directory_ver.replace("_", "")

    if customer_path:
        download_zpk_path = customer_path
    else:
        download_zpk_path = get_download_zpk_path(remote_directory)

    print(f"【DEBUG】download_zpk_path = {download_zpk_path}")
    """ 生成新的文件名 """
    current_date = datetime.date.today().strftime("%y%m%d")
    ver = get_version(download_zpk_path, current_date)

    file_name = f'WL_{directory_ver}_{current_date}' + ver
    print(f"【DEBUG】new file name = {file_name}")
    return file_name

def get_languages(remote_floder_name: str) -> list:
    """ 获取语言列表 """
    user_config_root = open_xml("./user_config.xml").getroot()
    # for child in user_config_root.findall("language"):
    #     if child.get("name") == "default_language":
    #         return child.get("range").split(",")
    remote_floder_name = str(remote_floder_name)
    for child in user_config_root.findall("language_config"):
        if remote_floder_name == child.get("name"):
            print("Getting language list for folder: ", remote_floder_name)
            return [x.strip() for x in child.get("range").split(",")]
    return ['LANGUAGE_ENGLISH']

def get_mode(remote_floder_name: str) -> str:
    """ 获取模式 """
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "mode_cfg_list":
            return child.get("value")

def set_language(language:str):
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "default_language":
            child.set("value", language)
    save_xml(user_config_root, "./user_config.xml")

async def modify_user_config(ssh_client, remote_directory, file_name):
    """修改user_config文件为最新的版本号"""
    sftp = await ssh_client.get_sftp()

    remote_user_conf_xml_path = get_text('remote_user_config_xml_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    async with sftp.open(remote_directory + remote_user_conf_xml_path, 'rb') as remote_user_conf_xml:
        try:
            # 异步读取文件内容（作为字节序列）
            xml_content = await remote_user_conf_xml.read()
            # 使用fromstring来解析XML数据，确保输入为字节序列
            remote_user_conf_tree = LXML_ET.fromstring(xml_content)
        except LXML_ET.XMLSyntaxError as e:
            print(f"XML解析错误：{e}")
            return
        except IOError as e:
            print(f"文件读取错误：{e}")
            return

        # 进行 XML 数据的修改操作
        element = remote_user_conf_tree.xpath('/config/item[@name="ZpkVersion"]')[0]
        element.set('value', file_name)  # 修改value属性

        root = open_xml("./user_config.xml").getroot()
        for child in root.findall("item"):
            # print(child.tag, child.attrib)
            for key, val in child.attrib.items():
                # print(key, val)
                if key == 'name':
                    print(f"{key} = {val}")
                    el_list = remote_user_conf_tree.xpath(f'/config/item[@name="{val}"]')
                    if el_list:
                        element = el_list[0]
                    else:
                        break    
                else: 
                    element.set(key, val)  # 修改value属性
                    print(f"Set {key} = {val}")

        # currencies = root.find("currencies_with_decimal").get("value")
        # element = remote_user_conf_tree.xpath('/config/item[@name="currencies_with_decimal"]')[0]
        # element.set('value', currencies)  # 修改value属性
        
        modified_xml = LXML_ET.tostring(remote_user_conf_tree, encoding="utf-8", xml_declaration=True)

        # 将修改后的 XML 字节序列写回文件
        async with sftp.open(remote_directory + remote_user_conf_xml_path, 'wb') as modified_file:
            await modified_file.write(modified_xml)


async def upload_currencys_xml(ssh_client:SSH_Client ,remote_directory:str):
    """ 上传货币配置文件 """
    try:
        sftp = await ssh_client.get_sftp()
        remote_currencys_xml_path = get_text('remote_currencys_xml_path',  scheme=get_scheme(remote_directory), config_tree="remote_config")
        await sftp.put(local_currencys_xml_path+'currencys.xml', remote_directory+remote_currencys_xml_path+'currencys.xml')
    except Exception as e:
        print(f"【Error】上传货币配置文件失败：{e}")

async def get_remote_ui_file_name(ssh_client:SSH_Client, remote_ui_file_path):
    try:
        sftp = await ssh_client.get_sftp()
        # 执行远程命令获取匹配的文件名
        result = await ssh_client.run_command(f'cd {remote_ui_file_path} && ls ui_resource*.bin')
        
        # 分析结果以获取文件名
        file_names = result.splitlines()
        # print(f"【Info】远程目录 {remote_ui_file_path} 下的文件名：{file_names}")
        print(f"【DEBUG】result = {result}")
        print(f"【DEBUG】file_names = {file_names}")
        if len(file_names) > 1:
            # 返回第一个文件名或根据需要处理多个文件
            for ui_file in file_names:
                ui_file = os.path.join(remote_ui_file_path, ui_file)
                print(f"【DEBUG】Delete ui_file = {ui_file}")
                await sftp.remove(ui_file)
            return None
        elif len(file_names) == 1:
            return file_names[0]
        else:
            print("No matching files found.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def upload_ui_file(ssh_client:SSH_Client ,remote_directory:str, ui_file:str):
    """ 上传ui文件 """
    try:
        sftp = await ssh_client.get_sftp()

        # remote_ui_file_name = get_text('remote_ui_file_name',  scheme=get_scheme(remote_directory), config_tree="remote_config")
        # if not remote_ui_file_name.endswith('.bin'):
        #     remote_ui_file_name += '.bin'


        local_ui_file_path = get_text('local_ui_file_path')
        remote_ui_file_path = get_text('remote_ui_file_path',  scheme=get_scheme(remote_directory), config_tree="remote_config")
        remote_ui_file_path = os.path.join(remote_directory, remote_ui_file_path)

        remote_ui_file_name = await get_remote_ui_file_name(ssh_client, remote_ui_file_path)

        if remote_ui_file_name is None:
            remote_ui_file_name = get_text('remote_ui_file_name',  scheme=get_scheme(remote_directory), config_tree="remote_config")

        print(f"【Info】上传{ui_file} -> {remote_ui_file_name}")
        await sftp.put(local_ui_file_path+ui_file, remote_ui_file_path+remote_ui_file_name)
    except Exception as e:
        print(f"【Error】上传{ui_file}失败：{e}")

async def set_auto_currency(ssh_client:SSH_Client ,remote_directory:str, currency_list:str):
    """ A33方案设置需要自动的货币 """
    if (get_scheme(remote_directory) != 'A33'):
        return
    
    sftp = await ssh_client.get_sftp()
    sys_config_xml_path = get_text('remote_system_config_xml_path',  scheme=get_scheme(remote_directory), config_tree="remote_config")

    async with sftp.open(remote_directory + sys_config_xml_path, 'rb') as remote_sys_config_xml:
        try:
            # 异步读取文件内容（作为字节序列）
            xml_content = await remote_sys_config_xml.read()
            # 使用fromstring来解析XML数据，确保输入为字节序列
            remote_sys_config_tree = LXML_ET.fromstring(xml_content)
        except LXML_ET.XMLSyntaxError as e:
            print(f"XML解析错误：{e}")
            return
        except IOError as e:
            print(f"文件读取错误：{e}")
            return
        # 定义命名空间映射
        namespaces = {'ns': 'AK47-BK1'}
        currency_list = currency_list.replace("AUT,MIX,", "")
        
        element = remote_sys_config_tree.xpath('//ns:Auto_Currency', namespaces=namespaces)
        if (element):
            element[0].set('current_inherit', currency_list)  # 修改value属性
            print(f"Set Auto_Currency = {currency_list}")
        else:
            print("No Auto_Currency element found.")

        modified_xml = LXML_ET.tostring(remote_sys_config_tree, encoding="utf-8", xml_declaration=True)

        # 将修改后的 XML 字节序列写回文件
        async with sftp.open(remote_directory + sys_config_xml_path, 'wb') as modified_file:
            await modified_file.write(modified_xml)

async def pack_zpk(ssh_client: SSH_Client, remote_directory: str, customer_path: str, callback):
    """打包zpk文件并下载"""
    sftp = await ssh_client.get_sftp()
    
    # 如果有输入客户代码，则下载到客户代码文件夹下
    if customer_path:
        file_name = generate_new_name(remote_directory, customer_path)
    else:
        file_name = generate_new_name(remote_directory)

    await modify_user_config(ssh_client, remote_directory, file_name)

    # 构建并执行命令来获取文件数量
    cmd_get_file_amount = f'cd {remote_directory}/upgrade; find . -type f | wc -l'
    file_count = await ssh_client.run_command(cmd_get_file_amount)
    file_count = int(file_count.strip())  # 转换成整数
    print(f"file_count={file_count}")

    # 生成新的文件名
    # file_name = generate_new_name(remote_directory)
    remote_run_script = get_text('remote_run_script', scheme=get_scheme(remote_directory), config_tree="remote_config")
    command = f"cd {remote_directory}; sh {remote_run_script} {file_name}"

    # 执行打包脚本
    await ssh_client.run_command_with_progress(command, file_count, callback)
    print(f"打包完成")


async def download_zpk(ssh_client: SSH_Client, remote_directory: str, customer_path: str, update_progress) -> str:
    # 建立 SFTP 客户端连接
    sftp = await ssh_client.get_sftp()

    # 执行命令获取最新的文件名
    get_latest_file_cmd = "ls -lt | head -n 2 | tail -n 1 | awk '{print $9}'"
    latest_file = await ssh_client.run_command(f"cd {remote_directory}; {get_latest_file_cmd}")

    # remote_file_path = f"{remote_directory}{latest_file}"  # 注意路径分隔符
    remote_file_path = os.path.join(remote_directory, latest_file)
    download_zpk_path = get_download_zpk_path(remote_directory)

    # 如果有输入客户代码，则下载到客户代码文件夹下
    if customer_path:
        local_file_path = os.path.join(customer_path, latest_file)
    else:
        local_file_path = os.path.join(download_zpk_path, latest_file)

    print(f"【DEBUG】local_file_path = {local_file_path}")
    # 获取远程文件的大小
    # remote_file_stat = await sftp.stat(remote_file_path)
    # total_size = remote_file_stat.size

    # 使用 SFTP 的 get 方法下载文件
    await sftp.get(remote_file_path, localpath=local_file_path, progress_handler=update_progress)
    if ".ZPK" in latest_file:
        await sftp.remove(remote_file_path)
    abs_path = os.path.abspath(local_file_path)
    copy_to_clipboard(abs_path)

    sftp.exit()
    print("ZPK文件下载完成：", local_file_path)
    return latest_file
