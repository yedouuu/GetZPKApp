import paramiko
import datetime
import os
from os import system
import xml.etree.ElementTree as ET
import lxml.etree as LXML_ET
from colorama import Fore, Style, init
from tqdm import tqdm
import time
"""
scp Administrator@192.168.0.117:/D:/200_WL/210_GL20双CIS/new/currencys.xml 
/home/lin/Desktop/LKR/upgrade/part/IMG_AUTO/
"""

def print_red_text(text):
    print(Fore.RED + text + Style.RESET_ALL)

def print_green_text(text):
    print(Fore.GREEN + text + Style.RESET_ALL)

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

def get_text(root, tag):
    """ 查找指定tag的值 """
    try:
        return root.find(tag).text
    except AttributeError as e:
        print_red_text(f"【ERROR】文件读取错误：{e}")
        print_red_text(f"【ERROR】文件读取错误：{tag}")
        input("按任意键退出...")
        exit()

def clear_screen():
    """ 清屏 """
    system('cls' if os.name == 'nt' else 'clear')

def map_ui_file_name(remote_directory):
    """ 
    1. /home/lin/Desktop/UN60_OLD/
    2. /home/lin/Desktop/UN60_NEW/
    3. /home/lin/Desktop/UN60_TOUCH/
    4. /home/lin/Desktop/UN60_DEV/
    根据选择的remote_directory, 返回所有ui_resource_xxx.bin文件 
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

def scanf_ui_file(current_folder, remote_directory):
    """ 
    根据选择的remote_directory, 返回所有ui_resource_xxx.bin文件 
    1. UN60_NEW      --> ui_resource_WLGL20.bin
    2. UN60_XXX      --> ui_resource_UN60_XXX.bin
    3. UN200_XXX    --> ui_resource_UN200_XXX.bin
    """
    # 获取当前文件夹下的所有文件
    contents = os.listdir(current_folder)
    ui_file_name = map_ui_file_name(remote_directory)
    ret = [content for content in contents if '.bin' in content and f"{ui_file_name}" in content]
    return ret

def select_ui_file(current_folder, remote_directory):
    """ 替换ui文件 """
    # 获取当前文件夹下的所有ui文件
    ui_files = scanf_ui_file(current_folder, remote_directory)
    
    if len(ui_files) == 0:
        print_red_text(f"当前文件夹下没有对应【{remote_directory.split('/')[-2]}】目录的UI文件")
        print_red_text(f"对应UI文件的命名应包含: {map_ui_file_name(remote_directory)}")
        input("按任意键退出...")
        exit()

    ret = ui_files[0]
	# 检查是否只有一个ui文件
    if ( len(ui_files) == 1 ):
        #print(f"当前选择的UI文件: {ui_files[0]}")
        ret = ui_files[0]
        return ret
    
    # 获取新的ui文件
    print("当前文件夹下的UI文件：")
    for i, ui_file in enumerate(ui_files):
        print(f"{i+1}. {ui_file}")
    
    print_green_text(f"当前选择的UI文件: {ret}")
    while True:
        s = input("请输入要替换的UI文件编号:")
        if s == "":
            clear_screen()
            return ret
        s = s.split()
        
        # 检查输入是否有效
        if len(s) == 0 or (len(s) == 1 and s[0] == ''):
            print_red_text("输入无效，请重新输入！")
            continue
        
        # 检查输入是否在有效范围内
        if int(s[0]) < 1 or int(s[0]) > len(ui_files):
            print_red_text("输入无效，请重新输入！")
            continue
        
        # 获取要替换的ui文件名
        ret = ui_files[int(s[0])-1]
        clear_screen()
        #print_green_text(f"当前选择的UI文件: {ui_file}")
        return ret

def get_remote_directory_version(remote_directory, type="ver"):
    """ 获取远端目录版本 
    type: "full" 返回完整文件名；"ver" 返回版本号
    return 
    1. /home/lin/Desktop/UN60_OLD/    -> OLD
    2. /home/lin/Desktop/UN60_NEW/    -> NEW
    3. /home/lin/Desktop/UN60_TOUCH/  -> TOUCH
    4. /home/lin/Desktop/UN60_DEV/    -> DEV
    """
    directory_name = remote_directory.split('/')[-2]
    if "full" in type:
        return directory_name.upper()
    elif "ver" in type:
        return directory_name.split('_')[-1].upper()



def select_remote_directory(root):
    """ 选择远端目录
    1. /home/lin/Desktop/UN60_OLD/
    2. /home/lin/Desktop/UN60_NEW/
    3. /home/lin/Desktop/UN60_TOUCH/
    4. /home/lin/Desktop/UN60_DEV/
    """
    try:
        remote_directories = root.findall('remote_directory')
        print("选择远端目录：")
        for i, remote_directory in enumerate(remote_directories):
            print(f"{i+1}. {remote_directory.text.split('/')[-2]}")

        remote_directory_name = remote_directories[0].text.split('/')[-2]
        print_green_text(f"当前选择的远端目录: {remote_directory_name}")
        
        local_currencys_xml_path = get_text(root, 'local_currencys_xml_path')
        currencys_xml_tree = open_xml(local_currencys_xml_path+"currencys.xml")
        country_code_list = get_open_country(currencys_xml_tree)
        print_green_text(f"当前选择的币种:  {country_code_list}")
        #输入回车表示使用默认值
        while True:
            s = input("请输入要选择的远端目录编号(默认为1):")
            if ( s == '' ):
                clear_screen()
                return remote_directories[0].text
            
            if s.isdigit():
                s = s.split()
                # 检查输入是否有效
                if len(s) == 0 or (len(s) == 1 and s[0] == ''):
                    print("输入无效，请重新输入！")
                    continue
                
                # 检查输入是否在有效范围内
                if int(s[0]) < 1 or int(s[0]) > len(remote_directories):
                    print("输入无效，请重新输入！")
                    continue
                
                # 获取要替换的ui文件名
                remote_directory = remote_directories[int(s[0])-1].text
            else:
                remote_directory = remote_directories[0].text.split('/')
                remote_directory[-2] = s
                remote_directory = '/'.join(remote_directory)

            clear_screen()
            print_green_text(f"当前选择的远端目录: {remote_directory}")
            print()
            return remote_directory
        
    except AttributeError as e:
        print_red_text(f"【ERROR】文件读取错误：{e}")
        print_red_text(f"【ERROR】在选择远端工作目录时出错：remote_directories = {remote_directories}")
        input("按任意键退出...")
    except Exception as e:
        print_red_text(f"【ERROR】未知错误：{e}")
        input("按任意键退出...")

def get_open_country(tree):
    """ 获取开启的国家 """
    country_code = []
    for e in tree.iter("Country"):
        tmp = e.find("selecttion").get("val")
        if tmp == "Y":
            country_code.append(e.get("tag"))
    return country_code

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

def download_file_via_sftp_with_tqdm(hostname, port, username, password, remote_file_path, local_file_path):
    """
    使用SFTP下载文件，并使用tqdm显示进度条。
    :param hostname: SFTP服务器主机名或IP地址
    :param port: SFTP端口号
    :param username: 用户名
    :param password: 密码
    :param remote_file_path: 远程文件路径
    :param local_file_path: 本地文件路径
    """
    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    # 创建SFTP客户端
    sftp = ssh.open_sftp()
    
    # 获取远程文件的大小
    remote_file_info = sftp.stat(remote_file_path)
    remote_file_size = remote_file_info.st_size

    # 创建tqdm进度条
    progress_bar = tqdm(total=remote_file_size, unit='B', unit_scale=True, desc="下载进度")

    def tqdm_callback(transferred, _):
        """
        更新tqdm进度条的回调函数。
        :param transferred: 已传输的数据量
        """
        progress_bar.update(transferred - progress_bar.n)

    # 下载文件
    sftp.get(remote_file_path, local_file_path, callback=tqdm_callback)
    
    # 关闭进度条
    progress_bar.close()

    # 关闭连接
    sftp.close()
    ssh.close()

    print("下载完成")

def path_valide(path):
    """ 检查路径是否有效 """
    if not path.endswith('/'):
        path += '/'
    return path

def main():
    tree = open_xml('./ssh_config.xml')
    # 解析XML文件
    root = tree.getroot()

    # SSH 连接参数
    hostname = get_text(root, 'hostname')
    username = get_text(root, 'username')
    port = get_text(root, 'port')
    password = get_text(root, 'password')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password)
    sftp = ssh.open_sftp()


    """ 1. 获取 currency.xml 文件 """

    local_currencys_xml_path = get_text(root, 'local_currencys_xml_path')
    remote_directory = select_remote_directory(root)
    remote_currencys_xml_path = get_text(root, 'remote_currencys_xml_path')

    currencys_xml_tree = open_xml(local_currencys_xml_path+"currencys.xml")
    country_code_list = get_open_country(currencys_xml_tree)
    
    
    """ 2. 获取 ui_resource_xxx.bin 文件 """
    local_ui_file_path = get_text(root, 'local_ui_file_path')
    ui_file = select_ui_file(local_ui_file_path, remote_directory)
    remote_ui_file_path = get_text(root, 'remote_ui_file_path')
    
    """ 3. Double Check """
    clear_screen()
    print_green_text(f"当前选择的远端目录: {remote_directory}")
    print_green_text(f"当前选择的UI文件:  {ui_file}")
    print_green_text(f"当前选择的币种:  {country_code_list}")
    
    _input = input("是否继续？(Y/n):")
    if _input.upper() == 'Y' or _input == "":
        pass
    else:
        print_red_text("退出程序")
        input("按任意键退出...")
        input("按任意键退出...")
        exit()

    """ 4. 上传 currency.xml 文件 """
    sftp.put(local_currencys_xml_path+'currencys.xml', remote_directory+remote_currencys_xml_path+'currencys.xml')
    
    """ 5. 替换ui文件 """
    # # 获取远端的ui文件名称
    # stdin, stdout, stderr = ssh.exec_command('cd ' + remote_directory+remote_ui_file_path + '; ' + 'ls -lt | grep "ui_resource_" | awk \'{print $9}\'')
    # remote_ui_file = stdout.read().decode().strip()
    
    # # 删除远端的ui文件
    # if ("ui_resource_" in remote_ui_file):
    #     print(f"【Info】删除 {remote_directory+remote_ui_file_path+remote_ui_file}")
    #     sftp.remove(remote_directory+remote_ui_file_path+remote_ui_file)
    
    remote_ui_file_name = get_text(root, 'remote_ui_file_name')
    if not remote_ui_file_name.endswith('.bin'):
        remote_ui_file_name += '.bin'

    print(f"【Info】上传{ui_file} -> {remote_ui_file_name}")
    sftp.put(local_ui_file_path+ui_file, remote_directory+remote_ui_file_path+remote_ui_file_name)
    
    """ 6.1 获取ZPK版本 """
    directory_ver = get_remote_directory_version(remote_directory, "full")
    directory_ver = directory_ver.replace("_", "")

    """ 6.2 在当前创建对应目录版本的文件夹 """
    local_zpk_path = path_valide(get_text(root, 'local_zpk_path'))

    download_zpk_path = path_valide(local_zpk_path + directory_ver)
    if not os.path.exists(download_zpk_path):
        os.makedirs(download_zpk_path)

    """ 6. 生成最新的文件名 """
    current_date = datetime.date.today().strftime("%y%m%d")
    ver = get_version(download_zpk_path, current_date)

    file_name = f'WL_{directory_ver}_{current_date}' + ver
    
    
    
    """ 7. 修改USER_CONFIG.XML """
    user_config_xml_path = get_text(root, 'remote_user_config_xml_path')
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

    """ 8. 执行脚本 """
    # 获取待处理的文件总数
    cmd_get_file_amount = f'cd {remote_directory}/upgrade; find . | wc -l'
    stdin, stdout, stderr = ssh.exec_command(cmd_get_file_amount)
    file_count = int(stdout.read().strip())

    sftp.chdir(remote_directory)
    get_latest_file = "ls -lt | head -n 2 | tail -n 1 | awk '{print $9}'"
    remote_run_script = root.find('remote_run_script').text
    
    command = f"cd {remote_directory}; sh {remote_run_script} {file_name}"
    
    # 打开一个SSH的channel
    channel = ssh.get_transport().open_session()
    channel.get_pty()
    channel.exec_command(command)

    # 初始化进度条和计数器
    with tqdm(total=file_count+10, desc="【Info】打包进度", unit="file") as pbar:
        last_update_time = time.time()
        buffered_updates = 0  # 缓存的更新次数
        data_buffer = ''
        while True:
            current_time = time.time()
            if channel.exit_status_ready(): 
                break
            if channel.recv_ready():
                data_chunk = channel.recv(1024).decode('utf-8')
                data_buffer += data_chunk  # 添加到缓冲区
                # 如果有完整的文件名（以换行符分隔）
                while '\n' in data_buffer:
                    # 分割出一个完整的文件名
                    filename, data_buffer = data_buffer.split('\n', 1)
                    filename = filename.strip()  # 清理空白字符
                    if filename:  # 如果文件名不为空
                        # print(filename)  # 打印文件名
                        buffered_updates += 1  # 更新缓存计数

            # 每0.5秒更新一次进度条
            if current_time - last_update_time >= 0.5:
                pbar.update(buffered_updates)  # 使用累积的更新次数刷新进度条
                buffered_updates = 0  # 重置缓存计数
                last_update_time = current_time

        # 确保在循环结束时更新进度条至最终状态
        pbar.update(buffered_updates)
    print()

    """ 9. 等待脚本执行完成, 获取ZPK """
    if channel.recv_exit_status() != 0:
        # 脚本执行失败时的错误处理
        print("【Error】: Remote command execution failed.")
        print(stderr.read().decode())
    else:
        """ 下载ZPK文件 """
        stdin, stdout, stderr = ssh.exec_command('cd ' + remote_directory + '; ' + get_latest_file)
        latest_file = stdout.read().decode().strip()
        print_green_text(f"【Info】下载{latest_file}")

        local_file_path = download_zpk_path + latest_file
        remote_file_path = remote_directory + latest_file
        download_file_via_sftp_with_tqdm(hostname, port, username, password, remote_file_path, local_file_path)
        # sftp.get(remote_directory+latest_file, local_currencys_xml_path + latest_file)

    # 获取命令输出
    output = stdout.read().decode()
    print(output)

    # 关闭 SSH 连接
    ssh.close()
    sftp.close()

    input("输入任意键关闭！")

if __name__ == '__main__':
    init()
    main()

