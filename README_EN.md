# calTodo

English | [中文](README.md)

Automatically sync your Outlook class calendar to a Microsoft To Do homework list.

## Features

- Read this week's classes from a specified Outlook Calendar (e.g., "Class Schedule")
- Calculate the current teaching week based on the school start date
- Auto-create homework reminders in a designated Microsoft To Do list
- Deduplicate tasks to avoid creating duplicates
- Task naming format: `Week{X}{CourseName}Homework`
- Due date automatically set to the Sunday of the current week

## Prerequisites

### 1. Register an Azure App

The script accesses your Outlook calendar and To Do via the Microsoft Graph API, so you need to register an app in Azure first:

1. Open [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**
2. **Name**: Fill in as you like (e.g., `calTodo`)
3. **Supported account types**: Select `Accounts in any organizational directory and personal Microsoft accounts`
4. Leave **Redirect URI** blank → Click **Register**
5. Copy the **Application (client) ID** — this is your `CLIENT_ID`
6. Left menu → **Authentication** → **Advanced settings** → Enable **Allow public client flows** → **Save**
7. Left menu → **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**
   - Search and add: `Calendars.Read`
   - Search and add: `Tasks.ReadWrite`
   - Click **Grant admin consent for ...** (for personal accounts, just confirm consent)

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file and fill in the following:

```env
CLIENT_ID=your-azure-app-client-id
TENANT_ID=common
CALENDAR_NAME=Class Schedule
TODO_LIST_NAME=Homework
SCHOOL_START_DATE=2025-02-17
```

- `CLIENT_ID`: The application ID copied from Azure Portal
- `TENANT_ID`: Use `common` for personal accounts, or your specific tenant ID for organizational accounts
- `CALENDAR_NAME`: The display name of your class calendar in Outlook
- `TODO_LIST_NAME`: The name of the Microsoft To Do list where tasks will be added
- `SCHOOL_START_DATE`: The school start date in `YYYY-MM-DD` format, used to calculate the teaching week

## Installation & Usage

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# First run: you will be prompted to sign in via browser
uv run main.py
```

On the first run, the terminal will display something like:

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code XXXXXXXX to authenticate.
```

Open the link, enter the code, and sign in with your Microsoft account to authorize. The token will be cached, so subsequent runs won't require re-login.

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install msgraph-sdk azure-identity python-dotenv
python main.py
```

## Automation (Optional)

You can schedule the script to run automatically every week:

- **Linux/macOS**: Use `crontab -e` to add a Monday morning job
  ```
  0 8 * * 1 cd /path/to/calTodo && uv run main.py
  ```
- **Windows**: Use "Task Scheduler" to create a weekly trigger

## Notes

- The script defaults to `China Standard Time`. Edit the `time_zone` parameter in `main.py` if needed
- If a course meets multiple times a week, a task is created for each occurrence (as homework may differ)
- If a task with the same title already exists, it will be skipped automatically to avoid duplicates
