import asyncio
import datetime
import os
import xml.etree.ElementTree as ET
import lxml.etree as LXML_ET
from colorama import Fore, Style, init
import time
from SSHClient import SSH_Client
from file_Utils import copy_to_clipboard

def print_red_text(text):
    init()
    print(Fore.RED + text + Style.RESET_ALL)
    try:
        with open("error_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"【{datetime.datetime.now()}】: {text}\n")
    except IOError as e:
        print(f"Error writing to log file: {e}")

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

def get_config_tree(config_tree="ssh_config"):
    """ 获取对应的xml树 """
    if "ssh_config" in config_tree:
        return ssh_config_tree
    elif "remote_config" in config_tree:
        return remote_config_tree
    else:
        print_red_text(f"【ERROR】未知的config_tree：{config_tree}")
        input("按任意键退出...")
        exit()

def get_tags(tag, scheme=None, config_tree="ssh_config"):
    """ 获取指定标签的所有子标签 """
    tree = get_config_tree(config_tree)
    if scheme is not None:
        xpath_expr = f"./IMG_DesignScheme[@val='{scheme}']"
        scheme_node = tree.find(xpath_expr)
        return scheme_node.findall(tag)
    else:
        return tree.findall(tag)

def get_text(tag, type="one", scheme=None, config_tree="ssh_config"):
    """ 查找指定tag的text值

    tag: 要查找的标签

    type:
        - one: (默认值)返回一个元素的text
        - all: 以List返回所有查找到的元素的text

    scheme: 对应的设计方案, 如: GL20, A33, 
        - remote_directory 和 remote_template_path 不需要指定 scheme

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
            if ("remote_directory" in tag) or ("remote_template_path" in tag) or \
               ("remote_currency_template_path" in tag) or ("remote_ui_file_template_path" in tag):
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
    扫描本地目录，查找与特定远程目录模式匹配的UI二进制文件（.bin），
    并过滤掉属于更高级别目录版本的文件。
    此函数执行以下步骤：
    1. 从配置中检索本地文件夹路径。
    2. 列出该本地文件夹中的所有文件。
    3. 将提供的 `remote_directory` 映射到特定的UI文件名模式。
    4. 识别类似的远程文件夹，并确定当前 `remote_directory` 的版本级别。
    5. 选择包含 '.bin' 和映射的UI文件名的初始候选文件。
    6. 过滤掉实际上属于类似文件夹的“更高级别”（更具体或更新）版本的文件，以避免歧义。
    参数：
        remote_directory (str): 用于确定目标UI文件名模式的远程目录标识符或路径字符串。
    返回：
        list: 在本地目录中找到的符合给定远程目录级别标准的文件名（字符串）列表。
    """
    
    # 获取当前文件夹下的所有文件
    current_folder = get_text("local_ui_file_path")
    contents = os.listdir(current_folder)
    ui_file_name = map_ui_file_name(remote_directory)
    simular_folders = [get_remote_directory_version(f, "full") for f in get_remote_directorys() if remote_directory in f]
    level = get_remote_directory_level(remote_directory)
    
    print(f"current_folder = {current_folder}")
    print(f"ui_file_name = {ui_file_name}")
    print(f"simular_folders = {simular_folders}")
    print(f"level = {level}")
    
    # 获取当前目录对应的ui文件
    ret = [content for content in contents if '.bin' in content and f"{ui_file_name}" in content]

    print(f"Found ui files({len(ret)})")

    # 移除高级别目录对应的ui文件    
    for folder in simular_folders:
        folder_level = get_remote_directory_level(folder)
        if folder_level > level:
            alt_ui_file_name = map_ui_file_name(folder)
            alt_files = [content for content in contents if '.bin' in content and f"{alt_ui_file_name}" in content]
            for alt_files in alt_files:
                if alt_files in ret:
                    ret.remove(alt_files)
        
    print(f"After filter ui files({len(ret)})")
    
    return ret

def get_remote_directorys():
    """ 获取所有远端目录列表 """
    # server = get_server()
    # paths  = []
    
    # for _remote_folder in server.findall("remote_directory"):
    #         print(f"Model: {_remote_folder.get('model')}")
    #         for path in _remote_folder.findall("path"):
    #             print(f"  Path: {path.text}")
    #             paths.append(path.text)
    # return paths
    return get_text("remote_directory", "all", config_tree="remote_config")

def get_remote_directory_level(remote_directory: str) -> int:
    """
    Docstring for get_remote_directory_level
    获取远端目录的级别
    <remote_directory IMGDesignScheme="GL20" level="1">/home/lin/Desktop/UN60/</remote_directory>
    <remote_directory IMGDesignScheme="GL20" level="2">/home/lin/Desktop/UN60_ZH/</remote_directory>
    
    Example: 
    UN60    -> level 1,
    UN60_ZH -> level 2
    
    :param remote_directory: Description
    :type remote_directory: str
    :return: Description
    :rtype: int
    """
    server = get_server()
    level = ""
    
    for _remote_folder in server.findall("remote_directory"):
        if remote_directory == get_remote_directory_version(_remote_folder.text, "full"):
            level = _remote_folder.get("level")
    
    if level == "":
        print_red_text(f"【ERROR】无法获取远端目录级别：{remote_directory}")
        print_red_text("将使用默认值level=1, 请检查remote_config.xml中的remote_directory配置")
        level = "1"
        
    return int(level)

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

def get_local_currencyXML_path():
    """ 获取本地currency.xml路径

    return origin_xml_path, new_xml_path
    """

    origin_xml_path = os.path.abspath(get_text("local_original_currencys_xml_path"))
    new_xml_path = os.path.abspath(get_text("local_currencys_xml_path"))
    new_xml_path = os.path.join(new_xml_path, "currencys.xml")

    return origin_xml_path, new_xml_path

def get_open_country(remote_folder:str = ""):
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


def get_version(remote_directory:str, current_folder, current_date):
    new_ver = 'A'
    
    contents = os.listdir(current_folder)  # Get the list of contents
    if len(contents) == 0:
        return new_ver
    # 获取当前文件夹下的所有文件
    if ( "GL18" == get_scheme(remote_directory)):
        file_subfix = "_GLImage.GIN"
        s = [content.split(file_subfix)[0][-1] for content in contents if (file_subfix in content) and (f"{current_date}" in content)]
    else:
        file_subfix = ".ZPK"
        s = [content.split('.')[0][-1] for content in contents if (file_subfix in content) and (f"{current_date}" in content)]

    print(f"Existing versions for date {current_date}: {s}")
    if len(s) > 0:
        max_s = max(s)
        new_ver = chr((ord(max_s) - ord('A') + 1) % 26 + ord('A'))
    
    return new_ver

def get_scheme(remote_folder:str):
    """ 获取远端目录的方案 """
    remote_folder = str(remote_folder)

    server = get_server()
    for _remote_folder in server.findall("remote_directory"):
        if remote_folder in _remote_folder.text:
            print(_remote_folder.text, "   ", _remote_folder.attrib["IMGDesignScheme"])
            return _remote_folder.attrib["IMGDesignScheme"]
    return None

def get_SyncICC(remote_folder:str) -> bool:
    """ 获取远端目录的SyncICC属性 """
    remote_folder = str(remote_folder)
    sync_icc = True

    server = get_server()
    for _remote_folder in server.findall("remote_directory"):
        if remote_folder in _remote_folder.text:
            tmp = _remote_folder.attrib.get("SyncICC", "True")
            print(f"{remote_folder} SyncICC = {tmp}")
            if (tmp.upper() == "FALSE"):
                sync_icc = False
                break
    
    return sync_icc


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


def generate_new_name(remote_directory:str, customer_path="", customer_code="WL"):
    """ 获取最新的文件名字 
    return: f'{customer_code}_{directory_ver}_{current_date}' + ver
    """

    """ 6.1 获取ZPK版本 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    
    """ 只取机型部分 UN60M_ENRU -> UN60M """
    directory_ver = directory_ver.split("_")[0]

    if customer_path:
        download_zpk_path = customer_path
    else:
        download_zpk_path = get_download_zpk_path(remote_directory)

    print(f"【DEBUG】download_zpk_path = {download_zpk_path}")
    """ 生成新的文件名 """
    current_date = datetime.date.today().strftime("%y%m%d")
    ver = get_version(remote_directory, download_zpk_path, current_date)
    motor_type = get_motor_type()
    language_code = get_language_code(get_language())

    file_name = f'{customer_code}_{directory_ver}_{motor_type}_{language_code}_{current_date}' + ver
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

def get_mode(remote_floder_name: str = "") -> str:
    """ 获取模式 """
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "mode_cfg_list":
            return child.get("value")
        
def GL18_get_base_proj_path():
    """ 获取GL18的基本项目路径 """
    base_proj_path = get_text("local_GL18_base_proj_path")
    base_proj_path = os.path.abspath(base_proj_path)
    print(f"【DEBUG】base_proj_path = {base_proj_path}")
    os.makedirs(base_proj_path, exist_ok=True)
    return base_proj_path


def GL18_get_image_app_path(remote_folder: str):
    ret = ""
    base_path = GL18_get_base_proj_path()
    image_app_path = get_text("local_image_app_path")
    image_app_path = os.path.join(base_path, remote_folder, image_app_path)
    image_app_path = os.path.abspath(image_app_path)
    print(f"【DEBUG】image_app_path = {image_app_path}")
    os.makedirs(image_app_path, exist_ok=True)

    for item in os.listdir(image_app_path):
        if item.endswith(".bin") and item.startswith("GL18"):
            ret = os.path.join(image_app_path, item)
            print(f"【DEBUG】ret = {ret}")
    return ret

def GL18_get_boot_path(remote_folder: str):
    ret = ""
    base_path = GL18_get_base_proj_path()
    boot_path = get_text("local_boot_path")
    boot_path = os.path.join(base_path, remote_folder, boot_path)
    print(f"【DEBUG】boot_path = {boot_path}")
    os.makedirs(boot_path, exist_ok=True)

    for item in os.listdir(boot_path):
        if item.endswith(".bin") and "BOOT" in item:
            ret = os.path.join(boot_path, item)
            print(f"【DEBUG】ret = {ret}")
    return ret

def GL18_get_mainboard_app_path(remote_folder: str):
    ret = ""
    base_path = GL18_get_base_proj_path()
    mainboard_app_path = get_text("local_mainboard_app_path")
    mainboard_app_path = os.path.join(base_path, remote_folder, mainboard_app_path)
    print(f"【DEBUG】mainboard_app_path = {mainboard_app_path}")
    os.makedirs(mainboard_app_path, exist_ok=True)

    for item in os.listdir(mainboard_app_path):
        if item.endswith(".bin") and item.startswith("M4"):
            ret = os.path.join(mainboard_app_path, item)
            print(f"【DEBUG】ret = {ret}")
    return ret

def set_language(language:str):
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "default_language":
            child.set("value", language)
    save_xml(user_config_root, "./user_config.xml")

def get_language() -> str:
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "default_language":
            return child.get("value")
    return "LANGUAGE_ENGLISH"

def get_language_code(language:str) -> str:
    """ 
    根据语言代码获取语言标识
    <language_code_map code="EN">LANGUAGE_ENGLISH</language_code_map>
    """
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("language_code_map"):
        if child.text == language:
            return child.get("code")

def set_motor_type(motor:str):
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "default_smotor_type":
            child.set("value", motor)
    save_xml(user_config_root, "./user_config.xml")

def get_motor_type(remote_folder:str = "") -> str:
    user_config_root = open_xml("./user_config.xml").getroot()
    for child in user_config_root.findall("item"):
        if child.get("name") == "default_smotor_type":
            return child.get("value")
    return ""



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


def need_mag_para(remote_folder):
    """
    Check if the specified remote folder requires mag_para.xml processing
    :param remote_folder: 远程文件夹(UN60_XXX, UN200)
    :return: True if mag_para.xml processing is needed, False otherwise
    """
    scheme = get_scheme(remote_folder)
    if scheme in ["A33", "GL20MULTI", "GL18"]:
        return True
    return False


async def upload_mag_para_xml(ssh_client:SSH_Client ,remote_directory:str):
    """ 上传mag_para.xml """
    if ( need_mag_para(remote_directory) == False ):
        print("No need to upload mag_para.xml")
        return
    
    try:
        sftp = await ssh_client.get_sftp()
        remote_mag_xml_path = get_text('remote_mag_xml_path',  scheme=get_scheme(remote_directory), config_tree="remote_config")
        local_mag_xml_file_path = get_text("local_new_mag_xml_file_path", scheme=get_scheme(remote_directory), config_tree="remote_config")
        await sftp.put(local_mag_xml_file_path, remote_directory+remote_mag_xml_path+'mag_para.xml')
    except Exception as e:
        print(f"【Error】上传mag_para.xml失败：{e}")

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
    """ A33方案设置需要自动的货币, 最多32个国家 """
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
        
        # 限制国家数量, 取前64个国家
        num = get_text('auto_detect_num', scheme=get_scheme(remote_directory), config_tree="remote_config")
        currency_list = ','.join(currency_list.split(',')[:int(num)])

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

def get_remote_template_path():
    """ 获取远端模板路径 """
    remote_template_path = get_text('remote_template_path', config_tree="remote_config")
    remote_template_path = remote_template_path[0]  # 取第一个路径
    return remote_template_path

def get_remote_currency_template_path():
    """ 获取远端货币模板路径 """
    remote_currency_template_path = get_text('remote_currency_template_path', config_tree="remote_config")
    remote_currency_template_path = remote_currency_template_path[0]  # 取第一个路径
    return remote_currency_template_path

async def sync_currencys_xml(ssh_client:SSH_Client) -> bool:
    """ 同步远端的currencys.xml到本地
    
    比较remote_currency_template_path 下所有文件和本地文件的修改时间, 只下载更新的文件
    
    1. 获取远端所有xml文件列表
    2. 逐个与本地xml文件对比
    3. 若远端文件修改时间更新, 则下载覆盖本地文件, 包含元信息
    4. 若本地文件不存在, 则直接下载
    
    return: 有无文件更新
    """
    updated = False
    
    sftp = await ssh_client.get_sftp()
    remote_currency_template_path = get_remote_currency_template_path()
    
    remote_currency_template_path = os.path.join(remote_currency_template_path).replace('\\', '/')
    local_currencys_xml_path = path_valide(get_text("local_original_currencys_xml_path"))
    
    
    print(f"Syncing currencys.xml files from {remote_currency_template_path} to {local_currencys_xml_path}")
    try:
        remote_files = await sftp.listdir(remote_currency_template_path)
        for remote_file in remote_files:
            if remote_file.endswith('.xml'):
                remote_file_path = os.path.join(remote_currency_template_path, remote_file).replace('\\', '/')
                local_file_path = os.path.join(local_currencys_xml_path, remote_file)
                
                # 获取远端文件的修改时间
                remote_attr = await sftp.stat(remote_file_path)
                remote_mtime = remote_attr.mtime
                
                # 获取本地文件的修改时间
                if os.path.exists(local_file_path):
                    local_mtime = os.path.getmtime(local_file_path)
                else:
                    local_mtime = 0  # 本地文件不存在
                
                # 比较修改时间
                if remote_mtime > local_mtime:
                    updated = True
                    print(f"Downloading updated file: {remote_file}")
                    await sftp.get(remote_file_path, local_file_path, preserve=True)
                else:
                    print(f"Local file is up-to-date: {remote_file}")
        return updated
    except Exception as e:
        print(f"Error syncing currencys.xml files: {e}")


async def sync_ui_files(ssh_client:SSH_Client):
    """ 同步远端的currencys.xml到本地
    
    比较remote_ui_file_path 下所有文件和本地文件的修改时间, 只下载更新的文件
    
    1. 获取远端所有 bin 文件列表
    2. 逐个与本地bin文件对比
    3. 若远端文件修改时间更新, 则下载覆盖本地文件, 包含元信息
    4. 若本地文件不存在, 则直接下载
    
    return: 有无文件更新
    """
    updated = False
    
    sftp = await ssh_client.get_sftp()
    remote_ui_file_path = get_text('remote_ui_file_template_path', config_tree="remote_config")
    remote_ui_file_path = remote_ui_file_path[0]  # 取第一个路径
    remote_ui_file_path = os.path.join(remote_ui_file_path).replace('\\', '/')
    
    local_ui_file_path = path_valide(get_text("local_ui_file_path"))
    
    print(f"Syncing UI files from {remote_ui_file_path} to {local_ui_file_path}")
    try:
        remote_files = await sftp.listdir(remote_ui_file_path)
        for remote_file in remote_files:
            if remote_file.endswith('.bin'):
                remote_file_path = os.path.join(remote_ui_file_path, remote_file).replace('\\', '/')
                local_file_path = os.path.join(local_ui_file_path, remote_file)
                
                # 获取远端文件的修改时间
                remote_attr = await sftp.stat(remote_file_path)
                remote_mtime = remote_attr.mtime
                
                # 获取本地文件的修改时间
                if os.path.exists(local_file_path):
                    local_mtime = os.path.getmtime(local_file_path)
                else:
                    local_mtime = 0  # 本地文件不存在
                
                # 比较修改时间
                if remote_mtime > local_mtime:
                    updated = True
                    print(f"Downloading updated file: {remote_file}")
                    await sftp.get(remote_file_path, local_file_path, preserve=True)
                else:
                    print(f"Local file is up-to-date: {remote_file}")
        return updated
    except Exception as e:
        print(f"Error syncing UI files: {e}")

async def create_currency_templates(ssh_client: SSH_Client, remote_directory: str, currency_list: str):
    """
    生成货币模板文件
    
    从 remote_template_path 路径下拷贝对应的文件到 remote_directory 路径下
    
    - bin_folder:    货币模板
    - xml_folder:    鉴伪区域配置
    - sensit_folder: 鉴伪灵敏度配置
    """
    
    sftp = await ssh_client.get_sftp()
    
    # 1. 获取远端模板路径
    remote_template_path = get_remote_template_path()
    
    remote_template_folder_tag = get_tags('remote_template_folder', scheme=get_scheme(remote_directory), config_tree="remote_config")
    remote_template_folder_tag = remote_template_folder_tag[0]

    remote_template_bin_folder       = remote_template_folder_tag.find(f"bin_folder").text
    remote_template_color_bin_folder = remote_template_folder_tag.find(f"color_bin_folder").text
    remote_template_xml_folder       = remote_template_folder_tag.find(f"xml_folder").text
    remote_template_sensit_folder    = remote_template_folder_tag.find(f"sensit_folder").text
    remote_template_ocr_folder       = remote_template_folder_tag.find(f"ocr_folder").text

    custom_xml_folder_tag = remote_template_folder_tag.find("custom_xml_folder")
    custom_xml_folder = None
    if custom_xml_folder_tag is not None:
        print(f"remote_custom_xml_folder = {custom_xml_folder_tag.text}")
        if custom_xml_folder_tag.attrib.get("model") in remote_directory:
            custom_xml_folder = custom_xml_folder_tag.text
            
    print(f"remote_template_path = {remote_template_path}")
    print(f"remote_template_bin_folder = {remote_template_bin_folder}")
    print(f"remote_template_color_bin_folder = {remote_template_color_bin_folder}")
    print(f"remote_template_xml_folder = {remote_template_xml_folder}")
    print(f"remote_template_sensit_folder = {remote_template_sensit_folder}")
    print(f"remote_template_ocr_folder = {remote_template_ocr_folder}")

    remote_template_bin_path        = os.path.join(remote_template_path, remote_template_bin_folder).replace('\\', '/')
    remote_template_color_bin_path  = os.path.join(remote_template_path, remote_template_color_bin_folder).replace('\\', '/')
    remote_template_xml_path        = os.path.join(remote_template_path, remote_template_xml_folder).replace('\\', '/')
    remote_template_sensit_path     = os.path.join(remote_template_path, remote_template_sensit_folder).replace('\\', '/')
    remote_template_ocr_path        = os.path.join(remote_template_path, remote_template_ocr_folder).replace('\\', '/')
    remote_template_custom_xml_path = None
    
    if custom_xml_folder is not None:
        remote_template_custom_xml_path = os.path.join(remote_template_path, custom_xml_folder).replace('\\', '/')
        print(f"remote_template_custom_xml_path = {remote_template_custom_xml_path}")
    
    remote_bin_path    = get_text('remote_bin_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    remote_xml_path    = get_text('remote_xml_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    remote_sensit_path = get_text('remote_sensit_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    remote_ocr_path    = get_text('remote_ocr_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    remote_color_bin_path = get_text('remote_color_bin_path', scheme=get_scheme(remote_directory), config_tree="remote_config")
    
    remote_bin_path = os.path.join(remote_directory, remote_bin_path)
    remote_xml_path = os.path.join(remote_directory, remote_xml_path)
    
    if remote_color_bin_path is not None:
        remote_color_bin_path = os.path.join(remote_directory, remote_color_bin_path)
    
    if remote_sensit_path is not None:
        remote_sensit_path = os.path.join(remote_directory, remote_sensit_path)
    
    if remote_ocr_path is not None:
        remote_ocr_path = os.path.join(remote_directory, remote_ocr_path)

    # 2. 移除原有的 remote_bin_path 和 remote_color_bin_path 下所有文件夹, 保留txt文件
    try:
        contents = await sftp.listdir(remote_bin_path)
        for content in contents:
            if not content.endswith('.txt') and content not in ['.', '..']:
                full_path = os.path.join(remote_bin_path, content).replace('\\', '/')
                print(f"Remove {full_path}")
                try:
                    # 使用SSH命令递归删除，比SFTP更可靠
                    await ssh_client.run_command(f'rm -rf "{full_path}"')
                    print(f"Successfully removed {full_path}")
                except Exception as e:
                    print(f"Error removing {full_path}: {e}")
    except Exception as e:
        print(f"Error while cleaning remote_bin_path: {e}")
        return

    if remote_color_bin_path is not None:
        try:
            contents = await sftp.listdir(remote_color_bin_path)
            for content in contents:
                if not content.endswith('.txt') and content not in ['.', '..']:
                    full_path = os.path.join(remote_color_bin_path, content).replace('\\', '/')
                    print(f"Remove {full_path}")
                    try:
                        # 使用SSH命令递归删除，比SFTP更可靠
                        await ssh_client.run_command(f'rm -rf "{full_path}"')
                        print(f"Successfully removed {full_path}")
                    except Exception as e:
                        print(f"Error removing {full_path}: {e}")
        except Exception as e:
            print(f"Error while cleaning remote_color_bin_path: {e}")
            return

    # 3. 拷贝对应的bin文件到 remote_directory 路径下
    """
    currency_list = "USD,CNY,EUR"
    1. 从 remote_template_path + remote_template_bin_folder 拷贝文件夹USD, CNY, EUR到 remote_bin_path
    """
    for currency in currency_list.split(','):
        if currency in ['AUT', 'MIX', 'AUTO', 'MULT']:
            continue
        
        if "GL20MULTI" == get_scheme(remote_directory):
            multi_remote_template_bin_path = os.path.join(remote_template_bin_path, currency)
            remote_currency_template_bin_path = os.path.join(multi_remote_template_bin_path, currency).replace('\\', '/')
        else:
            remote_currency_template_bin_path = os.path.join(remote_template_bin_path, currency).replace('\\', '/')
        
        remote_currency_bin_path = os.path.join(remote_bin_path, currency).replace('\\', '/')
        print(f"Copy {remote_currency_template_bin_path} -> {remote_currency_bin_path}")
        try:
            await ssh_client.run_command(f'cp -r "{remote_currency_template_bin_path}" "{remote_currency_bin_path}"')
            print(f"Successfully copied {currency} bin folder")
        except Exception as e:
            print(f"Error while copying {currency} bin folder: {e}")

    if remote_color_bin_path is not None:
        for currency in currency_list.split(','):
            remote_currency_template_color_bin_path = remote_template_color_bin_path.replace("XXX", currency)
            remote_currency_template_color_bin_path = os.path.join(remote_currency_template_color_bin_path, f"{currency}_color.bin").replace('\\', '/')
            remote_currency_color_bin_path = os.path.join(remote_color_bin_path, f"{currency}_color.bin").replace('\\', '/')
            print(f"Copy {remote_currency_template_color_bin_path} -> {remote_currency_color_bin_path}")
            try:
                await ssh_client.run_command(f'cp "{remote_currency_template_color_bin_path}" "{remote_currency_color_bin_path}"')
                print(f"Successfully copied {currency} color bin folder")
            except Exception as e:
                print(f"Error while copying {currency} color bin folder: {e}")

    # 4. 移除原有的 remote_xml_path 和 remote_sensit_path 下所有xml文件
    """
    只移除 XXX_ir_parameter.xml, XXX_sensitivity.xml 这样命名的文件
    """
    icc_xml_type = get_text('icc_xml_type', scheme=get_scheme(remote_directory), config_tree="remote_config")
    if icc_xml_type is None:
        icc_xml_type = '1'
    print(f"remote_directory = {remote_directory}, icc_xml_type = {icc_xml_type}")
    
    try:
        contents = await sftp.listdir(remote_xml_path)
        for content in contents:
            if content.endswith('.xml') and content not in ['.', '..']:
                full_path = os.path.join(remote_xml_path, content).replace('\\', '/')
                if '_ir_parameter.xml' in content or '_sensitivity.xml' in content:
                    print(f"Remove {full_path}")
                    try:
                        await ssh_client.run_command(f'rm -f "{full_path}"')
                        print(f"Successfully removed {full_path}")
                    except Exception as e:
                        print(f"Error removing {full_path}: {e}")
    except Exception as e:
        print(f"Error while cleaning remote_xml_path: {e}")
        return
    
    if icc_xml_type == '2' and remote_sensit_path is not None:
        try:
            contents = await sftp.listdir(remote_sensit_path)
            for content in contents:
                if content.endswith('.xml') and content not in ['.', '..']:
                    full_path = os.path.join(remote_sensit_path, content).replace('\\', '/')
                    if '_sensitivity.xml' in content:
                        print(f"Remove {full_path}")
                        try:
                            await ssh_client.run_command(f'rm -f "{full_path}"')
                            print(f"Successfully removed {full_path}")
                        except Exception as e:
                            print(f"Error removing {full_path}: {e}")
        except Exception as e:
            print(f"Error while cleaning remote_sensit_path: {e}")
            return

    # 5. 拷贝对应的xml文件到 remote_directory 路径下
    """
    currency_list = "USD,CNY,EUR"
    1. 先再 remote_template_custom_xml_path 中查找是否有对应的文件,
       有则拷贝 custom_xml_folder 下的文件到 remote_xml_path
    
    2. 若没有则从 remote_template_xml_path 拷贝文件 
       如: USD_ir_parameter.xml, CNY_ir_parameter.xml, EUR_ir_parameter.xml 到 remote_xml_path
    """
    
    for currency in currency_list.split(','):
        remote_currency_xml_template_path = os.path.join(remote_template_xml_path, f"{currency}_ir_parameter.xml").replace('\\', '/')
        remote_currency_sensit_template_path = os.path.join(remote_template_sensit_path, f"{currency}_sensitivity.xml").replace('\\', '/')
        
        if custom_xml_folder is not None:
            for file_name in await sftp.listdir(remote_template_custom_xml_path):
                if file_name in ['.', '..']:
                    continue
                if file_name == f"{currency}_ir_parameter.xml":
                    remote_currency_xml_template_path = os.path.join(remote_template_custom_xml_path, file_name).replace('\\', '/')
                elif icc_xml_type == '2' and file_name == f"{currency}_sensitivity.xml":
                    remote_currency_sensit_template_path = os.path.join(remote_template_custom_xml_path, file_name).replace('\\', '/')
                    print(f"Found custom sensitivity xml file for {currency}: {remote_currency_sensit_template_path}")
            
                print(f"Found custom xml file: {file_name} in {remote_template_custom_xml_path}")
        
        print(f"Copy {remote_currency_xml_template_path} -> {remote_xml_path}")
        
        if icc_xml_type == '2':
            print(f"Copy {remote_currency_sensit_template_path} -> {remote_sensit_path}")
        
        try:
            await ssh_client.run_command(f'cp "{remote_currency_xml_template_path}" "{remote_xml_path}"')
            print(f"Successfully copied {currency}_ir_parameter.xml")
            if icc_xml_type == '2':
                await ssh_client.run_command(f'cp "{remote_currency_sensit_template_path}" "{remote_sensit_path}"')
                print(f"Successfully copied {currency}_sensitivity.xml")
        except Exception as e:
            print(f"Error while copying {currency}_ir_parameter.xml or {currency}_sensitivity.xml: {e}")

    # 6. 拷贝OCR配置文件到 remote_directory 路径下
    """
    拷贝 remote_template_ocr_folder 下所有文件到 remote_ocr_path
    """
    if remote_template_ocr_folder is not None:
        try:
            for file_name in await sftp.listdir(remote_template_ocr_path):
                if file_name in ['.', '..']:
                    continue
                await ssh_client.run_command(f'cp "{os.path.join(remote_template_ocr_path, file_name).replace("\\", "/")}" "{remote_ocr_path}"')
            print(f"Successfully copied OCR configuration files from {remote_template_ocr_path} to {remote_ocr_path}")
        except Exception as e:
            print(f"Error while copying OCR configuration files: {e}")



async def pack_zpk(ssh_client: SSH_Client, remote_directory: str, customer_path, customer_code, callback):
    """打包zpk文件并下载"""
    sftp = await ssh_client.get_sftp()
    
    # 如果有输入客户代码，则下载到客户代码文件夹下
    if customer_path:
        file_name = generate_new_name(remote_directory, customer_path, customer_code)
    elif customer_code:
        file_name = generate_new_name(remote_directory, customer_code=customer_code)
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


async def download_zpk(ssh_client: SSH_Client, remote_directory: str, customer_path, update_progress) -> str:
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

async def main():
    # ssh_config = get_ssh_config()
    # ssh_client = SSH_Client(ssh_config["hostname"], \
    #                         ssh_config["port"],     \
    #                         ssh_config["username"], \
    #                         ssh_config["key_path"], \
    #                         ssh_config["password"] )
    # await ssh_client.connect()
    
    # # remote_directory = "/home/zpk/UN220M_ENRU/"
    # remote_directory = "/home/lin/Desktop/UN60M_ENRU/"
    # await create_currency_templates(ssh_client, remote_directory, "GBP,CNY,EUR,USD")
    
    # print(get_language_code("LANGUAGE_RUSSIAN"))
    # print(get_language_code("LANGUAGE_ENGLISH"))
    # print(get_language_code("LANGUAGE_POLISH"))
    
    # get_SyncICC("/home/lin/Desktop/UN60_NQS/")
    
    # remote_list = get_remote_directorys()
    # for remote_directory in remote_list:
    #     print(f"remote_directory = {remote_directory}")
    #     print(f"scheme = {get_scheme(remote_directory)}")
    #     print(f"level = {get_remote_directory_level(remote_directory)}")
    
    
    scan_ui_files("UN60")
    
    # print(await sync_currencys_xml(ssh_client))
    # await sync_ui_files(ssh_client)

if __name__ == '__main__':
    asyncio.run(main())
