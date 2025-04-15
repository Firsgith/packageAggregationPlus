import os
import subprocess
import shutil
from pathlib import Path

# 定义记录已同步路径的文件
SYNCED_PATHS_FILE = ".github/synced_paths"

def clean_existing_files(synced_paths):
    """
    清理主仓库中已存在的、由 .synced_paths 文件定义的文件或目录。
    :param synced_paths: 已同步的路径列表
    """
    print("Cleaning existing files and directories...")
    for target_path in synced_paths:
        target_path = os.path.join(".", target_path)
        if not target_path or os.path.abspath(target_path) == os.path.abspath("."):
            print(f"Skipping removal of current working directory: {target_path}")
            continue

        if os.path.exists(target_path):
            print(f"Removing existing path: {target_path}")
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

def is_submodule(temp_dir, sub_dir):
    """
    检查指定的子目录是否为子模块。
    :param temp_dir: 临时目录路径
    :param sub_dir: 子目录路径
    :return: True if the subdirectory is a submodule, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "-C", temp_dir, "submodule", "status", sub_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def handle_submodule(temp_dir, sub_dir):
    """
    如果子目录是子模块，手动克隆其内容。
    :param temp_dir: 临时目录路径
    :param sub_dir: 子目录路径
    :return: None
    """
    print(f"Detected '{sub_dir}' as a submodule. Cloning its contents...")
    submodule_url = subprocess.run(
        ["git", "-C", temp_dir, "config", "--get", f"submodule.{sub_dir}.url"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout.strip()

    if not submodule_url:
        print(f"Failed to retrieve URL for submodule '{sub_dir}'.")
        return

    # Clone the submodule's content into the same directory
    subprocess.run(["git", "clone", submodule_url, f"{temp_dir}/{sub_dir}"], check=True)

def parse_line(line):
    """
    解析一行输入，提取仓库地址、子目录路径和目标路径。
    :param line: 输入行
    :return: (repo_url, sub_dir, target_path)
    """
    line = line.strip().rstrip(";")  # 去掉末尾的分号
    if not line or line.startswith("#"):
        return None, None, None

    parts = line.split(",", 2)
    repo_url = parts[0].strip()
    sub_dir = parts[1].strip() if len(parts) > 1 else None
    target_path = None

    if len(parts) > 2 and "=" in parts[2]:
        target_path = parts[2].split("=")[1].strip()
    elif sub_dir:
        # 如果没有指定 path=，提取子目录路径的最后一个部分作为目标路径
        target_path = os.path.basename(sub_dir)

    return repo_url, sub_dir, target_path

def sync_repositories(packages_file):
    """
    同步 packages 文件中定义的仓库内容到主仓库。
    """
    print("Syncing repositories...")
    if not os.path.exists(packages_file):
        print(f"Error: {packages_file} not found.")
        return

    # 记录本次同步的路径
    synced_paths = []

    with open(packages_file, "r") as file:
        for line in file:
            repo_url, sub_dir, target_path = parse_line(line)
            if not repo_url:
                continue

            print(f"Parsing line: {line}")
            print(f"Repo URL: {repo_url}, Sub Dir: {sub_dir}, Target Path: {target_path}")

            # 提取仓库名称作为临时目录名
            repo_name = os.path.basename(repo_url).replace(".git", "")

            # 克隆仓库到临时目录
            temp_dir = f"/tmp/{repo_name}"
            print(f"Cloning {repo_url}...")
            try:
                subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to clone {repo_url}: {e}")
                continue

            # 删除 .git 目录
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)

            # 确定需要复制的源路径
            source_path = os.path.join(temp_dir, sub_dir) if sub_dir else temp_dir
            target_path = os.path.join(".", target_path or os.path.basename(source_path))

            # 检查源路径是否存在
            if not os.path.exists(source_path):
                print(f"Source path {source_path} does not exist, skipping...")
                shutil.rmtree(temp_dir)
                continue

            # 如果是子模块，手动克隆其内容
            if is_submodule(temp_dir, sub_dir):
                handle_submodule(temp_dir, sub_dir)

            # 确保目标路径的父目录存在
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)

            # 清理目标路径（仅删除当前路径，不删除父目录）
            if os.path.exists(target_path):
                print(f"Cleaning up existing target path: {target_path}")
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

            # 复制文件到目标路径
            print(f"Copying folder {source_path} to {target_path}...")
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)

            # 记录本次同步的路径
            synced_paths.append(os.path.relpath(target_path, "."))

            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"Synced {repo_name} successfully.")

    # 更新 .synced_paths 文件
    with open(SYNCED_PATHS_FILE, "w") as file:
        for path in synced_paths:
            file.write(f"{path}\n")

if __name__ == "__main__":
    # 主仓库根目录下的 packages 文件路径
    packages_file = "packages"

    # 清理已存在的内容
    if os.path.exists(SYNCED_PATHS_FILE):
        with open(SYNCED_PATHS_FILE, "r") as file:
            synced_paths = [line.strip() for line in file if line.strip()]
        clean_existing_files(synced_paths)

    # 同步新的内容
    sync_repositories(packages_file)
