import os
import subprocess
import shutil
from pathlib import Path

# 定义记录已同步路径和哈希值的文件
SYNCED_PATHS_FILE = ".github/synced_paths"
PACKAGES_FILE = "packages"

def get_remote_hash(repo_url):
    """
    获取远程仓库的最新提交哈希值。
    :param repo_url: 仓库地址
    :return: 最新提交哈希值
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo_url, "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.split()[0]  # 提取哈希值
        else:
            print(f"Failed to fetch remote hash for {repo_url}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error fetching remote hash for {repo_url}: {e}")
        return None

def parse_line(line):
    """
    解析一行输入，提取仓库地址、子目录路径、目标路径、克隆深度和哈希值。
    :param line: 输入行
    :return: (repo_url, sub_dir, target_path, depth, hash_value)
    """
    line = line.strip().rstrip(";")  # 去掉末尾的分号
    if not line or line.startswith("#"):
        return None, None, None, None, None

    parts = line.split(",")
    repo_url = parts[0].strip()  # 第一部分：仓库地址
    sub_dir = None
    target_path = None
    depth = None
    hash_value = None

    # 提取仓库名（去掉 .git 后缀）
    repo_name = os.path.basename(repo_url).replace(".git", "")

    # 遍历剩余部分，处理子目录路径、目标路径、克隆深度和哈希值
    for part in parts[1:]:
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip() == "path":
                target_path = value.strip()
            elif key.strip() == "depth":
                try:
                    depth = int(value.strip())  # 将 depth 转换为整数
                except ValueError:
                    print(f"Invalid depth value: {value}. Using default full clone.")
                    depth = None
            elif key.strip() == "hash":
                hash_value = value.strip()
        else:
            # 如果没有 path= 或 depth=，则认为这是子目录路径
            sub_dir = part

    # 目标路径的生成逻辑
    if target_path:
        if sub_dir:
            # 如果有子目录路径，则目标路径为 path/sub_dir的最后一部分
            target_path = os.path.join(target_path, os.path.basename(sub_dir))
        else:
            # 如果没有子目录路径，则目标路径为 path/仓库名
            target_path = os.path.join(target_path, repo_name)
    elif sub_dir:
        # 如果没有指定目标路径，则使用子目录的最后一部分
        target_path = os.path.basename(sub_dir)
    else:
        # 如果既没有目标路径也没有子目录路径，则默认为目标路径为仓库名
        target_path = repo_name

    # 如果没有子目录路径，默认同步整个仓库
    if not sub_dir:
        sub_dir = None

    return repo_url, sub_dir, target_path, depth, hash_value

def update_packages_file(packages_file, repo_url, new_hash):
    """
    更新 packages 文件中的哈希值。
    :param packages_file: packages 文件路径
    :param repo_url: 仓库地址
    :param new_hash: 新的哈希值
    """
    with open(packages_file, "r") as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if line.strip().startswith(repo_url):
            # 替换或添加 hash= 参数
            parts = line.split(",")
            updated_parts = []
            hash_found = False
            for part in parts:
                if part.strip().startswith("hash="):
                    updated_parts.append(f"hash={new_hash}")
                    hash_found = True
                else:
                    updated_parts.append(part.strip())
            if not hash_found:
                updated_parts.append(f"hash={new_hash}")
            updated_line = ", ".join(updated_parts) + ";\n"
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    with open(packages_file, "w") as file:
        file.writelines(updated_lines)

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
        for i, line in enumerate(file):
            repo_url, sub_dir, target_path, depth, saved_hash = parse_line(line)
            if not repo_url:
                continue

            # 打印解析规则前的空行（跳过第一条规则前的空行）
            if i > 0:
                print()

            # 打印解析结果
            print(f"Parsing line: {line.strip()}")
            print(f"Repo URL: {repo_url}, Sub Dir: {sub_dir}, Target Path: {target_path}, Depth: {depth}, Saved Hash: {saved_hash}")

            # 获取远程仓库的最新哈希值
            latest_hash = get_remote_hash(repo_url)
            if not latest_hash:
                print(f"Skipping {repo_url} due to failure in fetching remote hash.")
                continue

            # 如果哈希值未变化，跳过同步
            if saved_hash and saved_hash == latest_hash:
                print(f"No changes detected for {repo_url}. Skipping sync.")
                continue

            # 清理目标路径
            if os.path.exists(target_path):
                print(f"Cleaning up existing target path: {target_path}")
                try:
                    if os.path.isdir(target_path):
                        shutil.rmtree(target_path)
                    else:
                        os.remove(target_path)
                except Exception as e:
                    print(f"Error cleaning up target path {target_path}: {e}")

            # 克隆仓库到临时目录
            repo_name = os.path.basename(repo_url).replace(".git", "")
            temp_dir = f"/tmp/{repo_name}"
            print(f"Cloning {repo_url} with depth={depth}...")
            try:
                if depth:
                    subprocess.run(["git", "clone", "--depth", str(depth), repo_url, temp_dir], check=True)
                else:
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

            # 确保目标路径的父目录存在
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)

            # 复制文件到目标路径
            print(f"Copying folder {source_path} to {target_path}...")
            try:
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            except Exception as e:
                print(f"Error copying folder {source_path} to {target_path}: {e}")
                continue

            # 记录本次同步的路径
            synced_paths.append(os.path.relpath(target_path, "."))

            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"Synced {repo_name} successfully.")

            # 更新 packages 文件中的哈希值
            update_packages_file(packages_file, repo_url, latest_hash)

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
