import asyncio
from dulwich import porcelain
from dulwich.repo import Repo
import os

from SSHClient import SSH_Client
from xml_Utils import get_ssh_config


async def pull_remote_repo(ssh_client: SSH_Client, repo_path_on_server: str):
    """
    在远程服务器上对指定的 Git 仓库执行 git pull。

    :param ssh_client: 已连接的 SSH_Client 实例。
    :param repo_path_on_server: Git 仓库在服务器上的绝对路径。
    :param branch: 要拉取的分支名。
    """
    # 构造要在服务器上执行的命令
    # 1. cd 到仓库目录
    # 2. 执行 git pull
    command = f"cd {repo_path_on_server} && git pull"
    
    print(f"【INFO】将在服务器上执行: {command}")
    
    try:
        result = await ssh_client.run_command(command)
        
        print(f"【SUCCESS】服务器仓库 '{repo_path_on_server}' 拉取成功。")
        
        print("--- Git 输出 ---")
        print(result)
    

    except Exception as e:
        print(f"【ERROR】在服务器上执行 git pull 时出错: {e}")


async def pull_repo(repo_path, remote_name="origin", branch_name="master"):
    """
    使用 Dulwich 实现类似于 `git pull` 的功能。
    
    :param repo_path: 本地仓库路径
    :param remote_name: 远程仓库名称（默认为 "origin"）
    :param branch_name: 分支名称（默认为 "main"）
    """
    # 打开本地仓库
    repo = Repo(repo_path)

    porcelain.pull(repo, remote_name, branch_name)

    print(f"分支 '{branch_name}' 已成功同步到最新版本。")


async def main():
    # --- 使用示例 ---
    # 1. 获取SSH配置并连接
    ssh_config = get_ssh_config()
    ssh_client = SSH_Client(ssh_config["hostname"], \
                                     ssh_config["port"],     \
                                     ssh_config["username"], \
                                     ssh_config["key_path"], \
                                     ssh_config["password"]
                                    )
    await ssh_client.connect()

    # 2. 定义服务器上的仓库路径
    remote_repo_path = "/home/lin/Desktop/TEST_ICC/WL_ICC_Template" # 请替换为服务器上实际的仓库路径

    # 3. 调用函数执行 git pull
    await pull_remote_repo(ssh_client, remote_repo_path)

    # 4. 关闭连接
    await ssh_client.close()

if __name__ == "__main__":
    # Example usage
    # repo_path = "./WL_GL18_PackProj/"
    # repo_path = r"E:\Python_Proj\GetZPK\WL_GL18_PackProj"
    # pull_repo(os.path.abspath(repo_path))
    
    asyncio.run(main())