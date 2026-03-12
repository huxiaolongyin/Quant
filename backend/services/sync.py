"""进行数据同步的服务（APScheduler 任务入口 + 同步编排）

- 日线：使用 backend.core.provider.get_price(code, end_date, count, frequency="1d", fields=[])
- 节假日：GET https://publicapi.xiaoai.me/holiday/year?date={year}

实现要点：
1) 用 PostgreSQL 做"互斥锁 + 游标(sync_state)"：避免定时任务重入、支持增量同步
2) 日线按 trade_date 增量 upsert（unique_together = stock_code + trade_date）
3) 失败可重试/可续跑：cursor 只在成功后推进
"""

import asyncio
from datetime import date, datetime, timedelta

import httpx
from tortoise.transactions import in_transaction
from tqdm.asyncio import tqdm

from backend.core.logger import logger
from backend.core.provider import get_price
from backend.enums.sync import SyncStatus
from backend.models import DailyLine, Holiday, Stock, SyncConfig, SyncLog
from backend.schemas import PaginatedData
from backend.schemas.market import DateBar
from backend.schemas.sync import SchedulerInfo, SyncLogItem, SyncSummaryResponse


class SyncService:
    """接口服务，提供给接口"""

    async def sync_holidays(self):
        """
        同步节假日数据，会定时调度
        """
        current_year = datetime.now().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year + 1, 1, 1)

        existing = await Holiday.filter(date__gte=year_start, date__lt=year_end).exists()
        if existing:
            logger.info(f"已存在{current_year}节假日信息，跳过同步")
            return

        url = f"https://publicapi.xiaoai.me/holiday/year?date={current_year}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()

        data = data.get("data", [])

        holidays = [item for item in data if item.get("rest") == 1]

        for holiday in holidays:
            await Holiday.update_or_create(date=holiday["date"], defaults={"name": holiday["holiday"]})
        logger.info(f"{current_year}节假日信息同步完成")

    async def sync_stock_daily_line(self, start_date: datetime, end_date: datetime):
        """
        批量同步日线数据，会定时调度
        """
        trade_days = 0
        current = start_date

        holidays = await Holiday.filter(date__gte=start_date, date__lte=end_date).values_list("date", flat=True)
        holiday_set = set(holidays)

        while current <= end_date:
            if current.weekday() < 5 and current not in holiday_set:
                trade_days += 1
            current += timedelta(days=1)

        stock_objs = await Stock.all()

        stock_codes = [stock.full_stock_code for stock in stock_objs]

        all_data: list[DateBar] = []
        for code in tqdm(stock_codes, desc="获取股票数据"):
            data: list[DateBar] = get_price(code, end_date=end_date, count=trade_days)
            all_data.extend(data)
            await asyncio.sleep(0.05)

        new_records = [
            DailyLine(
                stock_code=item.stock_code,
                trade_date=item.trade_date,
                open=item.open_,
                close=item.close,
                high=item.high,
                low=item.low,
                volume=item.volume,
            )
            for item in all_data
            if not item or item.trade_date >= start_date.date()
        ]

        async with in_transaction() as conn:
            await DailyLine.bulk_create(
                new_records,
                using_db=conn,
                on_conflict=["stock_code", "trade_date"],
                update_fields=["open", "high", "low", "close", "volume", "turnover"],
            )
            logger.info(f"批量插入 {len(new_records)} 条记录成功")

    async def get_summary(self) -> SyncSummaryResponse:
        """
        返回同步状态、指标和调度器信息
        """
        config = await SyncConfig.first()
        if not config:
            config = await SyncConfig.create()

        last_log = await SyncLog.filter(status=SyncStatus.SUCCESS).first()

        daily_line_count = await DailyLine.all().count()
        stock_count = await Stock.all().count()

        first_record = await DailyLine.first()
        last_record = await DailyLine.last()

        if first_record and last_record:
            data_range = f"{first_record.trade_date} ~ {last_record.trade_date}"
            stat_days = (last_record.trade_date - first_record.trade_date).days
        else:
            data_range = "-"
            stat_days = 0

        return SyncSummaryResponse(
            last_sync_time=int(last_log.end_time.timestamp()) if last_log and last_log.end_time else 0,
            data_range=data_range,
            stat_days=stat_days,
            stock_count=stock_count,
            scheduler=SchedulerInfo(enabled=config.scheduler_enabled, time=config.scheduler_time),
            status=config.current_status,
        )

    async def get_logs(self, page: int = 1, page_size: int = 10) -> PaginatedData[SyncLogItem]:
        """
        获取数据同步日志
        """
        total = await SyncLog.all().count()
        logs = await SyncLog.all().offset((page - 1) * page_size).limit(page_size)

        items = [
            SyncLogItem(
                id=str(log.id),
                type=log.type,
                range=log.range_desc or "-",
                start_time=log.start_time.strftime("%Y-%m-%d %H:%M:%S") if log.start_time else "-",
                duration=log.duration(),
                status=log.status,
            )
            for log in logs
        ]

        return PaginatedData.create(items=items, total=total, page=page, page_size=page_size)

    async def update_scheduler_config(self, enabled: bool, time: str) -> SyncConfig:
        """
        更新调度配置
        """
        config = await SyncConfig.first()
        if not config:
            config = await SyncConfig.create(scheduler_enabled=enabled, scheduler_time=time)
        else:
            config.scheduler_enabled = enabled
            config.scheduler_time = time
            await config.save()

        logger.info(f"调度配置已更新: enabled={enabled}, time={time}")
        return config


sync_service = SyncService()
