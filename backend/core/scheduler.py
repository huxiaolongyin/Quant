from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.tasks import sync_holidays

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# 每年1月1日 00:00 执行
scheduler.add_job(sync_holidays, "cron", month=1, day=1, hour=0, minute=0)
