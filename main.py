import asyncio
import os
import sys
from datetime import date, datetime, time, timedelta

from dotenv import load_dotenv
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.calendars.item.calendar_view.calendar_view_request_builder import (
    CalendarViewRequestBuilder,
)
from msgraph.generated.models.todo_task import TodoTask
from msgraph.generated.models.todo_task_list import TodoTaskList
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone


def get_teaching_week(start_date_str: str) -> int:
    """根据开学日期计算当前是第几周."""
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = date.today()
    delta = today - start
    week = delta.days // 7 + 1
    return max(1, week)


def get_week_range(today: date) -> tuple[datetime, datetime]:
    """获取本周周一 00:00 到周日 23:59 的时间范围."""
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    start = datetime.combine(monday, time.min)
    end = datetime.combine(sunday, time.max)
    return start, end


async def find_target_calendar(client: GraphServiceClient, calendar_name: str):
    """在用户的日历中查找指定名称的日历."""
    calendars = await client.me.calendars.get()
    if not calendars or not calendars.value:
        return None

    for cal in calendars.value:
        if cal.name == calendar_name:
            return cal
    return None


async def find_or_create_todo_list(client: GraphServiceClient, list_name: str):
    """查找或创建指定名称的 To Do 列表."""
    todo_lists = await client.me.todo.lists.get()
    if todo_lists and todo_lists.value:
        for lst in todo_lists.value:
            if lst.display_name == list_name:
                return lst

    # 未找到则创建
    new_list = TodoTaskList(display_name=list_name)
    return await client.me.todo.lists.post(new_list)


async def get_existing_task_titles(client: GraphServiceClient, list_id: str) -> set[str]:
    """获取指定 To Do 列表中已有任务的标题集合."""
    tasks = await client.me.todo.lists.by_todo_task_list_id(list_id).tasks.get()
    if not tasks or not tasks.value:
        return set()
    return {t.title for t in tasks.value if t.title}


async def main():
    load_dotenv()

    client_id = os.getenv("CLIENT_ID")
    tenant_id = os.getenv("TENANT_ID", "common")
    calendar_name = os.getenv("CALENDAR_NAME", "课程表")
    todo_list_name = os.getenv("TODO_LIST_NAME", "作业")
    school_start_date = os.getenv("SCHOOL_START_DATE")

    if not client_id:
        print("错误: 请在 .env 文件中设置 CLIENT_ID")
        sys.exit(1)
    if not school_start_date:
        print("错误: 请在 .env 文件中设置 SCHOOL_START_DATE")
        sys.exit(1)

    credential = DeviceCodeCredential(
        client_id=client_id,
        tenant_id=tenant_id,
    )
    scopes = ["Calendars.Read", "Tasks.ReadWrite"]
    client = GraphServiceClient(credentials=credential, scopes=scopes)

    today = date.today()
    week_start, week_end = get_week_range(today)
    teaching_week = get_teaching_week(school_start_date)

    print(f"本周是第 {teaching_week} 教学周")
    print(f"查询时间范围: {week_start.isoformat()} ~ {week_end.isoformat()}")

    # 查找课程日历
    target_calendar = await find_target_calendar(client, calendar_name)
    if not target_calendar:
        calendars = await client.me.calendars.get()
        available = [cal.name for cal in calendars.value] if calendars and calendars.value else []
        print(f"错误: 未找到名为 '{calendar_name}' 的日历")
        print(f"可用日历: {available}")
        sys.exit(1)

    print(f"找到日历: {target_calendar.name}")

    # 获取本周课程事件
    query_params = CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
        start_date_time=week_start.isoformat(),
        end_date_time=week_end.isoformat(),
    )
    config = CalendarViewRequestBuilder.CalendarViewRequestBuilderGetRequestConfiguration(
        query_parameters=query_params
    )

    events = await client.me.calendars.by_calendar_id(
        target_calendar.id
    ).calendar_view.get(request_configuration=config)

    if not events or not events.value:
        print("本周没有课程，无需创建任务")
        return

    print(f"本周共有 {len(events.value)} 个课程事件")

    # 查找或创建 To Do 列表
    target_list = await find_or_create_todo_list(client, todo_list_name)
    print(f"目标列表: {target_list.display_name}")

    # 获取已有任务标题（去重）
    existing_titles = await get_existing_task_titles(client, target_list.id)

    # 截止日期设为当周周日 23:59
    sunday = today - timedelta(days=today.weekday()) + timedelta(days=6)
    sunday_end = datetime.combine(sunday, time(23, 59))
    due_date = DateTimeTimeZone(
        date_time=sunday_end.isoformat(),
        time_zone="China Standard Time",
    )

    created_count = 0
    skipped_count = 0

    for event in events.value:
        subject = event.subject or "未命名课程"
        task_title = f"第{teaching_week}周{subject}作业"

        if task_title in existing_titles:
            print(f"  跳过（已存在）: {task_title}")
            skipped_count += 1
            continue

        task = TodoTask(
            title=task_title,
            due_date_time=due_date,
        )

        await client.me.todo.lists.by_todo_task_list_id(target_list.id).tasks.post(task)
        print(f"  创建任务: {task_title}")
        created_count += 1

    print(f"\n完成: 创建 {created_count} 个新任务，跳过 {skipped_count} 个已存在任务")


if __name__ == "__main__":
    asyncio.run(main())
