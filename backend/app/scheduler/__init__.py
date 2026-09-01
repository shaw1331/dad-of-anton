from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.jobs import run_scheduled_stock_analysis

logger = logging.getLogger(__name__)

SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0
SCHEDULE_TIMEZONE = "Asia/Kolkata"


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=SCHEDULE_TIMEZONE)

    scheduler.add_job(
        run_scheduled_stock_analysis,
        trigger=CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, timezone=SCHEDULE_TIMEZONE),
        id="daily_stock_analysis",
        name="Daily stock analysis",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — stock analysis will run daily at %02d:%02d %s",
        SCHEDULE_HOUR,
        SCHEDULE_MINUTE,
        SCHEDULE_TIMEZONE,
    )
    return scheduler
