"""进行数据同步的服务（APScheduler 任务入口 + 同步编排）

- 日线：使用 backend.core.provider.get_price(code, end_date, count, frequency="1d", fields=[])
- 节假日：GET https://publicapi.xiaoai.me/holiday/year?date={year}

实现要点：
1) 用 PostgreSQL 做“互斥锁 + 游标(sync_state)”：避免定时任务重入、支持增量同步
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
from backend.models import DailyLine, Holiday, Stock
from backend.schemas.market import DateBar


class SyncService:
    """接口服务，提供给接口"""

    async def sync_holidays(self):
        """
        同步节假日数据，会定时调度
        """
        current_year = datetime.now().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year + 1, 1, 1)

        # 如果有今年的数据则跳过
        existing = await Holiday.filter(date__gte=year_start, date__lt=year_end).exists()
        if existing:
            logger.info(f"已存在{current_year}节假日信息，跳过同步")
            return

        url = f"https://publicapi.xiaoai.me/holiday/year?date={current_year}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()

        data = data.get("data", [])
        # 返回格式：[{"daytype": 1, "holiday": "元旦节", "rest": 1, "date": "2026-01-01", "week": 4, "week_desc_en": "Thursday", "week_desc_cn": "星期四" }...]

        holidays = [item for item in data if item.get("rest") == 1]

        for holiday in holidays:
            await Holiday.update_or_create(date=holiday["date"], defaults={"name": holiday["holiday"]})
        logger.info(f"{current_year}节假日信息同步完成")

    async def sync_stock_daily_line(self, start_date: datetime, end_date: datetime):
        """
        批量同步日线数据，会定时调度
        """
        # 1. 计算增量区间
        trade_days = 0
        current = start_date

        # 获取日期范围内的所有节假日
        holidays = await Holiday.filter(date__gte=start_date, date__lte=end_date).values_list("date", flat=True)
        holiday_set = set(holidays)

        while current <= end_date:
            # 排除周六周日（weekday() 5=周六, 6=周日）
            if current.weekday() < 5 and current not in holiday_set:
                trade_days += 1
            current += timedelta(days=1)

        # 2. 股票列表获取
        stock_objs = await Stock.all()

        # 测试用例
        # example_stocks = ["000001.SZ", "002106.SZ", "002327.SZ"]
        # stock_objs = await Stock.filter(full_stock_code__in=example_stocks)
        stock_codes = [stock.full_stock_code for stock in stock_objs]

        # 3. 获取股票数据
        all_data: list[DateBar] = []
        for code in tqdm(stock_codes, desc="获取股票数据"):
            data: list[DateBar] = get_price(code, end_date=end_date, count=trade_days)
            all_data.extend(data)
            await asyncio.sleep(0.05)  # 避免获取频繁，导致服务异常

        # 4. 过滤退市数据、空数据
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

        # 5. 插入或更新到数据库
        async with in_transaction() as conn:
            await DailyLine.bulk_create(
                new_records,
                using_db=conn,
                on_conflict=["stock_code", "trade_date"],
                update_fields=["open", "high", "low", "close", "volume", "turnover"],
            )
            logger.info(f"批量插入 {len(new_records)} 条记录成功")

        # 6. 更新游标

    async def get_summary(self):
        """
        返回同步状态、指标和调度器信息
        """
        ...

    async def get_logs(self, *args, **kwargs):
        """
        获取数据同步日志
        """
        ...


sync_service = SyncService()
