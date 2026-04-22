# calTodo

[English](README_EN.md) | 中文

自动将 Outlook 课程日历同步到 Microsoft To Do 作业列表。

## 功能

- 从 Outlook Calendar 读取指定日历（如"课程表"）的本周课程
- 根据开学日期计算当前教学周数
- 在 Microsoft To Do 的指定列表中自动创建作业提醒
- 自动去重，避免重复创建已存在的任务
- 任务命名格式：`第X周{课程名}作业`
- 截止日期自动设为当周周日

## 前置准备

### 1. 注册 Azure 应用

脚本通过 Microsoft Graph API 访问你的 Outlook 日历和 To Do，需要先在 Azure 注册一个应用：

1. 打开 [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
2. **Name** 随意填写（如 `calTodo`）
3. **Supported account types** 选择：`Accounts in any organizational directory and personal Microsoft accounts`
4. **Redirect URI** 留空 → 点击 **Register**
5. 复制 **Application (client) ID**，这就是 `CLIENT_ID`
6. 左侧菜单 → **Authentication** → **Advanced settings** → 启用 **Allow public client flows** → **Save**
7. 左侧菜单 → **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**
   - 搜索并添加：`Calendars.Read`
   - 搜索并添加：`Tasks.ReadWrite`
   - 点击 **Grant admin consent for ...**（个人账号点击后确认同意即可）

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下信息：

```env
CLIENT_ID=你的Azure应用客户端ID
TENANT_ID=common
CALENDAR_NAME=课程表
TODO_LIST_NAME=作业
SCHOOL_START_DATE=2025-02-17
```

- `CLIENT_ID`: 从 Azure Portal 复制的应用 ID
- `TENANT_ID`: 个人账号用 `common`，组织账号用具体租户 ID
- `CALENDAR_NAME`: Outlook 中课程日历的显示名称
- `TODO_LIST_NAME`: Microsoft To Do 中要添加任务的列表名称
- `SCHOOL_START_DATE`: 开学日期，格式 `YYYY-MM-DD`，用于计算教学周

## 安装与运行

### 使用 uv（推荐）

```bash
# 安装依赖
uv sync

# 首次运行，会提示在浏览器中登录授权
uv run main.py
```

首次运行时，终端会显示如下提示：

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code XXXXXXXX to authenticate.
```

打开链接，输入代码，登录你的 Microsoft 账号并授权即可。授权信息会缓存，后续运行无需再次登录。

### 使用 pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install msgraph-sdk azure-identity python-dotenv
python main.py
```

## 自动化（可选）

你可以将脚本加入系统的定时任务，每周自动执行：

- **Linux/macOS**: 使用 `crontab -e` 添加每周一早晨的任务
  ```
  0 8 * * 1 cd /path/to/calTodo && uv run main.py
  ```
- **Windows**: 使用"任务计划程序"创建每周触发器

## 注意事项

- 脚本默认使用 `China Standard Time` 作为时区，如需修改请编辑 `main.py` 中的 `time_zone` 参数
- 同一门课一周多次上课时，每次都会创建一个任务（因为每次课的作业可能不同）
- 如果任务已存在（按标题完全匹配），会自动跳过，避免重复
