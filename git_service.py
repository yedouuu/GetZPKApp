from dulwich import porcelain
from dulwich.repo import Repo
import os

def pull_repo(repo_path, remote_name="origin", branch_name="master"):
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


if __name__ == "__main__":
    # Example usage
    # repo_path = "./WL_GL18_PackProj/"
    repo_path = r"E:\Python_Proj\GetZPK\WL_GL18_PackProj"
    pull_repo(os.path.abspath(repo_path))