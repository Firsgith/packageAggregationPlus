# **GitHub Actions：同步包并清理工作流运行记录**

该存储库包含一个 GitHub Actions 工作流，用于自动从存储库中同步包，并清理旧的工作流运行记录。以下是设置和使用此工作流的说明。


## **功能**
1. **同步包**：
   - 自动运行 Python 脚本（`sync_packages.py`）以从存储库中同步包。
   - 将更改提交并推送到主分支。

2. **清理旧的工作流运行记录**：
   - 仅保留 `main` 分支上的最新 3 条工作流运行记录。
   - 删除较旧的运行记录以减少混乱并节省存储空间。


## **先决条件**

### **1. 所需权限**
为确保工作流正常运行，您需要配置以下权限：

#### **个人访问令牌 (PAT)**
- 创建一个具有以下作用域的 PAT：
  - `repo`：对私有存储库的完全控制。
  - `admin:org`：对组织资源的完全控制。
- 将 PAT 存储在存储库的 Secrets 中，名称为 `SYNC_TOKEN`。

#### **存储库设置**
1. 进入存储库的 **Settings > Secrets and variables > Actions**。
2. 点击 **New repository secret**。
3. 设置名称为 `SYNC_TOKEN`，并粘贴您的 PAT 值。
4. 保存 Secret。

1. 进入存储库的 **Settings > Actions > General**。
2. 在 **Workflow permissions** 下，选择 **Read and write permissions**。
   - 这允许工作流推送更改并删除工作流运行记录。
3. 启用 **Allow GitHub Actions to create and approve pull requests**。
   - 这确保工作流有足够的权限执行提交更改和删除运行记录等操作。


## **工作原理**
1. **触发工作流**：
   - 可通过 **workflow_dispatch** 事件手动触发，或在推送至 `main` 分支时自动触发。

2. **同步包**：
   - 工作流会检出存储库，设置 Python 3.10，并运行 `sync_packages.py` 脚本。
   - 脚本所做的任何更改都会通过 `SYNC_TOKEN` 提交并推回存储库。

3. **清理工作流运行记录**：
   - 工作流会获取 `main` 分支上的所有运行记录，并仅保留最新的 3 条。
   - 较旧的运行记录会被删除以减少混乱并节省存储空间。


## **故障排除**

### **1. 权限错误**
- 如果在清理步骤中遇到 `403 Forbidden` 错误：
  - 确保 `SYNC_TOKEN` 具有正确的范围（`repo` 和 `admin:org`）。
  - 确保在存储库设置中启用了 **Read and write permissions**。
  - 确保启用了 **Allow GitHub Actions to create and approve pull requests**。

### **2. 无效的运行 ID**
- 如果清理步骤跳过了某些运行 ID：
  - 检查 API 响应，确保提取了正确的 ID。
  - 添加调试日志以打印 API 响应：
    ```bash
    echo "API Response: $RESPONSE"
    ```


## **贡献**
如果您发现问题或有任何改进建议，请随时提交问题或发起拉取请求。


## **许可证**
本项目采用 MIT 许可证。有关详细信息，请参阅 [LICENSE](LICENSE) 文件。


---


# **GitHub Actions: Sync Packages and Clean Up Workflow Runs**

This repository contains a GitHub Actions workflow that automates the process of syncing packages from repositories and cleaning up old workflow runs. Below are the instructions for setting up and using this workflow.


## **Features**
1. **Sync Packages**:
   - Automatically run a Python script (`sync_packages.py`) to sync packages from repositories.
   - Commit and push changes back to the main branch.

2. **Clean Up Old Workflow Runs**:
   - Retain only the latest 3 workflow runs on the `main` branch.
   - Delete older workflow runs to reduce clutter and save storage space.


## **Prerequisites**

### **1. Required Permissions**
To ensure the workflow functions correctly, you need to configure the following permissions:

#### **Personal Access Token (PAT)**
- Create a PAT with the following scopes:
  - `repo`: Full control of private repositories.
  - `admin:org`: Full control of organization resources.
- Store the PAT in your repository's secrets as `SYNC_TOKEN`.

#### **Repository Settings**
1. Go to **Settings > Secrets and variables > Actions** in your repository.
2. Click **New repository secret**.
3. Set the name as `SYNC_TOKEN` and paste the value of your PAT.
4. Save the secret.

1. Go to **Settings > Actions > General** in your repository.
2. Under **Workflow permissions**, select **Read and write permissions**.
   - This allows the workflow to push changes and delete workflow runs.
3. Enable **Allow GitHub Actions to create and approve pull requests**.
   - This ensures the workflow has sufficient permissions to perform actions like committing changes and deleting runs.


## **How It Works**
1. **Triggering the Workflow**:
   - The workflow can be triggered manually via the **workflow_dispatch** event or automatically when pushing to the `main` branch.

2. **Syncing Packages**:
   - The workflow checks out the repository, sets up Python 3.10, and runs the `sync_packages.py` script.
   - Any changes made by the script are committed and pushed back to the repository using the `SYNC_TOKEN`.

3. **Cleaning Up Workflow Runs**:
   - The workflow fetches all runs on the `main` branch and retains only the latest 3 runs.
   - Older runs are deleted to reduce clutter and save storage space.


## **Troubleshooting**

### **1. Permission Errors**
- If you encounter `403 Forbidden` errors during the cleanup step:
  - Verify that the `SYNC_TOKEN` has the correct scopes (`repo` and `admin:org`).
  - Ensure **Read and write permissions** is selected under **Workflow permissions** in your repository settings.
  - Ensure **Allow GitHub Actions to create and approve pull requests** is enabled.

### **2. Invalid Run IDs**
- If the cleanup step skips Run IDs:
  - Check the API response to ensure the correct IDs are being extracted.
  - Add debug logs to print the API response:
    ```bash
    echo "API Response: $RESPONSE"
    ```


## **Contributing**
If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.


## **License**
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

