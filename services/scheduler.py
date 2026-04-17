#services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.queries import get_income, get_expenses

scheduler = AsyncIOScheduler()

async def daily_report(bot, user_id):
    income = get_income(user_id)
    expenses = get_expenses(user_id)

    await bot.send_message(user_id,
        f"📅 Отчет:\nДоход: {income}\nРасход: {expenses}")

def start_scheduler(bot, users):
    for user in users:
        scheduler.add_job(daily_report, "cron", hour=20, args=(bot, user))

    scheduler.start()