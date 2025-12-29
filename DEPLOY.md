# 部署教程 - GitHub + Render

## 目录
1. [本地准备](#1-本地准备)
2. [上传到 GitHub](#2-上传到-github)
3. [在 Render 部署](#3-在-render-部署)
4. [配置环境变量](#4-配置环境变量)
5. [测试和访问](#5-测试和访问)

---

## 1. 本地准备

### 1.1 确认项目文件完整

确保项目目录包含以下文件：
```
math_explorer_agent_english/
├── server.py           # Flask 服务器
├── config.py           # 配置文件
├── agent.py            # Agent 核心
├── models.py           # 数据模型
├── memory.py           # 内存管理
├── llm_client.py       # LLM 客户端
├── requirements.txt    # Python 依赖
├── Procfile            # Render 启动配置
├── .gitignore          # Git 忽略规则
├── .env.example        # 环境变量示例
├── website/            # 前端文件
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── prompts/            # 提示词文件
├── actions/            # Action 模块
└── memory_snapshots/   # 示例数据（可选）
```

### 1.2 创建本地 .env 文件

```bash
cd d:\Code\AI\math_explorer_agent_english
copy .env.example .env
```

编辑 `.env` 文件，填入你的真实 API 密钥：
```
API_KEY=sk-你的密钥
BASE_URL=https://ai.paratera.com/v1
MODEL=DeepSeek-V3.2
```

### 1.3 本地测试

```bash
python server.py
```

访问 http://localhost:5000/website/ 确认正常运行。

---

## 2. 上传到 GitHub

### 2.1 创建 GitHub 仓库

1. 打开 https://github.com
2. 点击右上角 **+** → **New repository**
3. 填写信息：
   - Repository name: `math-explorer-agent`
   - Description: `LLM-based mathematical exploration agent`
   - 选择 **Public** 或 **Private**
   - **不要**勾选 "Add a README file"
4. 点击 **Create repository**

### 2.2 安装 Git（如果未安装）

下载并安装：https://git-scm.com/download/win

### 2.3 初始化并推送代码

打开 PowerShell，执行以下命令：

```powershell
# 进入项目目录
cd d:\Code\AI\math_explorer_agent_english

# 初始化 Git 仓库
git init

# 添加所有文件（.gitignore 会自动排除 .env）
git add .

# 查看将要提交的文件（确认没有 .env）
git status

# 提交代码
git commit -m "Initial commit: Math Explorer Agent with web visualization"

# 设置主分支名称
git branch -M main

# 添加远程仓库（替换为你的用户名）
git remote add origin https://github.com/你的用户名/math-explorer-agent.git

# 推送代码
git push -u origin main
```

### 2.4 验证上传

1. 刷新 GitHub 仓库页面
2. 确认文件已上传
3. **重要**：确认 `.env` 文件**没有**被上传（应该只有 `.env.example`）

---

## 3. 在 Render 部署

### 3.1 注册 Render 账号

1. 打开 https://render.com
2. 点击 **Get Started for Free**
3. 可以选择 **Sign up with GitHub**（推荐，更方便）

### 3.2 创建新的 Web Service

1. 登录后，点击 **New +** → **Web Service**
2. 选择 **Build and deploy from a Git repository**
3. 点击 **Connect GitHub**，授权 Render 访问你的仓库
4. 找到并选择 `math-explorer-agent` 仓库
5. 点击 **Connect**

### 3.3 配置服务

填写以下信息：

| 设置项 | 值 |
|--------|-----|
| **Name** | `math-explorer-agent` |
| **Region** | 选择离你最近的区域（如 Singapore） |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn server:app --bind 0.0.0.0:$PORT --timeout 600` |

### 3.4 选择实例类型

- 选择 **Free** 免费计划
- 免费计划每月有 750 小时运行时间
- 注意：免费计划有 15 分钟无活动后休眠机制

---

## 4. 配置环境变量

### 4.1 添加环境变量

在 Render 的服务配置页面：

1. 滚动到 **Environment Variables** 部分
2. 点击 **Add Environment Variable**
3. 添加以下变量：

| Key | Value |
|-----|-------|
| `API_KEY` | 你的 API 密钥（如 sk-xxx） |
| `BASE_URL` | `https://ai.paratera.com/v1` |
| `MODEL` | `DeepSeek-V3.2` |
| `DEBUG` | `false` |

### 4.2 保存并部署

1. 点击 **Create Web Service**
2. Render 会自动开始构建和部署
3. 等待部署完成（通常需要 2-5 分钟）

---

## 5. 测试和访问

### 5.1 获取公网地址

部署成功后，Render 会分配一个公网地址，格式如：
```
https://math-explorer-agent.onrender.com
```

### 5.2 访问网站

打开浏览器访问：
```
https://你的应用名.onrender.com/website/
```

### 5.3 首次访问注意

- 免费计划首次访问可能需要等待 30-60 秒（冷启动）
- 如果显示加载中，请耐心等待

### 5.4 测试功能

1. 点击 **Start Exploration** 按钮
2. 输入一个数学问题
3. 点击开始探索
4. 观察是否正常工作

---

## 常见问题

### Q: 部署失败，显示 "Build failed"

检查 `requirements.txt` 是否正确，确保所有依赖都已列出。

### Q: 网站打开是空白页

检查浏览器控制台（F12）是否有错误，可能是环境变量未配置正确。

### Q: API 调用失败

确认 `API_KEY` 环境变量设置正确，检查 API 密钥是否有效。

### Q: 如何更新代码？

本地修改后：
```bash
git add .
git commit -m "Update: 描述你的修改"
git push
```
Render 会自动重新部署。

---

## 安全提醒

⚠️ **永远不要**把 API 密钥提交到 Git！

- `.env` 文件已被 `.gitignore` 忽略
- 只有 `.env.example`（不含真实密钥）会上传
- 真实密钥只存在于：
  - 本地 `.env` 文件
  - Render 环境变量

---

## 费用说明

| 项目 | 费用 |
|------|------|
| Render 托管 | 免费（750 小时/月） |
| GitHub 仓库 | 免费 |
| API 调用 | 根据你的 API 提供商计费 |

**注意**：公网用户访问你的网站并触发探索会消耗你的 API 额度！
