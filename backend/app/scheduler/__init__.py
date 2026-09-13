from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.jobs import run_scheduled_stock_analysis, refresh_open_trade_prices

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

    scheduler.add_job(
        refresh_open_trade_prices,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour="9,11,13,15",
            minute=30,
            timezone=SCHEDULE_TIMEZONE,
        ),
        id="open_trade_cmp",
        name="Open trade CMP refresh",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — stock analysis daily %02d:%02d, CMP refresh Mon-Fri 09:30/11:30/13:30/15:30 %s",
        SCHEDULE_HOUR,
        SCHEDULE_MINUTE,
        SCHEDULE_TIMEZONE,
    )
    return scheduler
