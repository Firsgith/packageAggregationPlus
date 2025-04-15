import os
import subprocess
import shutil

# 定义记录已同步路径的文件
SYNCED_PATHS_FILE = ".github/synced_paths"

def clean_existing_files():
    """
    清理主仓库中已存在的、由 .synced_paths 文件定义的文件或目录。
    """
    print("Cleaning existing files and directories...")
    if not os.path.exists(SYNCED_PATHS_FILE):
        print(f"No synced paths found in {SYNCED_PATHS_FILE}. Skipping cleanup.")
        return

    with open(SYNCED_PATHS_FILE, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            target_path = os.path.join(".", line)

            # 跳过当前工作目录（"."）
            if os.path.abspath(target_path) == os.path.abspath("."):
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
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith("#"):
                continue

            # 分割仓库地址、子目录路径和目标路径
            if ";" not in line:
                print(f"Invalid line format: {line}")
                continue
            line = line.rstrip(";")  # 去掉末尾的分号
            parts = line.split(",", 2)
            repo_url = parts[0].strip()
            folder_path = parts[1].strip() if len(parts) > 1 else None
            target_path = parts[2].split("=")[1].strip() if len(parts) > 2 and "=" in parts[2] else None

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
            source_path = os.path.join(temp_dir, folder_path) if folder_path else temp_dir
            target_path = os.path.join(".", target_path or os.path.basename(source_path))

            # 检查源路径是否存在
            if not os.path.exists(source_path):
                print(f"Source path {source_path} does not exist, skipping...")
                shutil.rmtree(temp_dir)
                continue

            # 如果是子模块，手动克隆其内容
            if is_submodule(temp_dir, folder_path):
                handle_submodule(temp_dir, folder_path)

            # 复制文件到目标路径
            print(f"Copying folder {source_path} to {target_path}...")
            if os.path.exists(target_path):
                shutil.rmtree(target_path)  # 如果目标路径已存在，先删除
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
    clean_existing_files()

    # 同步新的内容
    sync_repositories(packages_file)
