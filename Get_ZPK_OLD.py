import paramiko
import datetime
import os
import xml.etree.ElementTree as ET
from tqdm import tqdm
import time

"""
虚拟机ip：192.168.189.129
本机ip：192.168.0.117

scp Administrator@192.168.0.117:/D:/200_WL/210_GL20双CIS/new/currencys.xml 
/home/lin/Desktop/LKR/upgrade/part/IMG_AUTO/
"""

try:
    tree = ET.parse('./ssh_config.xml')
    # 在这里可以继续处理已解析的XML数据
except ET.ParseError as e:
    print(f"XML解析错误：{e}")
    input("按任意键退出...")
    exit()
except IOError as e:
    print(f"文件读取错误：{e}")
    input("按任意键退出...")
    exit()
config_root = tree.getroot()

def get_version(current_folder, current_date):
    contents = os.listdir(current_folder)  # Get the list of contents
    s = [content.split('.')[0][-1] for content in contents if 'ZPK' in content and f"{current_date}" in content]
    if len(s) > 0:
        max_s = max(s)
        new_ver = chr((ord(max_s) - ord('A') + 1) % 26 + ord('A'))
    else:
        new_ver = 'A'
    return new_ver


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

def scan_ui_files(folder):
    ui_path = config_root.find('local_ui_file_path').text
    return [file for file in os.listdir(ui_path) if file.endswith('.bin') and folder in file]

def get_country_code():
    return ['USD', 'EUR', "AED"]


def get_remote_folder_ver(folder_path):
    return folder_path.split('/')[-2]

def get_remote_folders() -> list:
    return [ get_remote_folder_ver(folder.text) for folder in config_root.findall("remote_directory")]

def Get_ZPK_OLD_main():
    # try:
    #     tree = ET.parse('./ssh_config.xml')
    #     # 在这里可以继续处理已解析的XML数据
    # except ET.ParseError as e:
    #     print(f"XML解析错误：{e}")
    #     input("按任意键退出...")
    #     exit()
    # except IOError as e:
    #     print(f"文件读取错误：{e}")
    #     input("按任意键退出...")
    #     exit()
    # root = tree.getroot()
    root = config_root
    # SSH 连接参数
    hostname = root.find('hostname').text
    username = root.find('username').text
    port = root.find('port').text
    password = root.find('password').text
    private_key_path = root.find('private_key_path').text

    # 创建一个SSH客户端对象
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 如果填写了私钥路径则使用私钥连接，否则使用密码连接
    if private_key_path:
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        ssh.connect(hostname, port=port, username=username, pkey=private_key)
    else:
        ssh.connect(hostname, port=port, username=username, password=password)

    # 执行命令

    # 上传 currency.xml 文件
    local_currencys_xml_path = root.find('local_currencys_xml_path').text
    remote_directory = root.find('remote_directory').text
    remote_xml_path = 'upgrade/part/IMG_AUTO/'
    sftp = ssh.open_sftp()
    sftp.put(local_currencys_xml_path+'currencys.xml', remote_directory+remote_xml_path+'currencys.xml')

    sftp.chdir(remote_directory)

    get_latest_file = "ls -lt | head -n 2 | tail -n 1 | awk '{print $9}'"

    """ 执行生成脚本 """
    remote_run_script = root.find('remote_run_script').text
    current_date = datetime.date.today().strftime("%y%m%d")

    ver = get_version(local_currencys_xml_path, current_date)

    file_name = f'WLGL20_{current_date}' + ver

    # 获取待处理的文件总数
    cmd_get_file_amount = f'cd {remote_directory}/upgrade; find . | wc -l'
    stdin, stdout, stderr = ssh.exec_command(cmd_get_file_amount)
    file_count = int(stdout.read().strip())

    command = 'cd ' + remote_directory + '; sh ' + remote_run_script + ' ' + file_name

    # stdin, stdout, stderr = ssh.exec_command(command)
    
    # 打开一个SSH的channel
    channel = ssh.get_transport().open_session()
    channel.get_pty()
    
    channel.exec_command(command)

    # 获取脚本输出
    # Read and print the output from stdout
    # for line in stdout:
    #     print(line.strip())

    # for line in iter(stdout.readline, ''):
    #     print(line, end='')

    
    # 初始化进度条和计数器
    # 
    with tqdm(total=file_count+10, desc="【Info】打包进度", unit="file") as pbar:
        last_update_time = time.time()
        buffered_updates = 0  # 缓存的更新次数
        data_buffer = ''
        while True:
            current_time = time.time()
            if channel.exit_status_ready(): 
                break
            if channel.recv_ready():
                # output = channel.recv(1024).decode('utf-8')
                # print(output.replace('\r\n', ' ').strip().split(' '), end='\n')  # 打印输出
                # buffered_updates += len(output.replace('\r\n', ' ').strip().split(' '))  # 增加缓存计数

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

    # 等待脚本执行完成
    # exit_status = stdout.channel.recv_exit_status()
    if channel.recv_exit_status() != 0:
        # 脚本执行失败时的错误处理
        print("【Error】: Remote command execution failed.")
        print(stderr.read().decode())
    else:
        """ 下载ZPK文件 """
        stdin, stdout, stderr = ssh.exec_command('cd ' + remote_directory + '; ' + get_latest_file)
        latest_file = stdout.read().decode().strip()

        local_file_path = local_currencys_xml_path + latest_file
        remote_file_path = remote_directory + latest_file
        print(f"【Info】下载{latest_file}")
        download_file_via_sftp_with_tqdm(hostname, port, username, password, remote_file_path, local_file_path)

    # 关闭 SSH 连接
    ssh.close()
    sftp.close()

    input("输入任意键关闭！")

if __name__ == '__main__':
    print(scan_ui_files("UN60_OLD"))
    # Get_ZPK_OLD_main()
    pass

