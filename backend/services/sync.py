from datetime import datetime, timedelta
from typing import Any, Dict, List

from tortoise.transactions import in_transaction

from backend.core.logger import logger
from backend.core.provider import get_price
from backend.enums.sync import SyncStatus, SyncType
from backend.models import DailyLine, Stock, SyncConfig, SyncLog
from backend.schemas import PaginatedData, SyncSummaryResponse


async def sync_stock_daily_line(symbol: str, start_date: datetime, end_date: datetime):
    """
    同步日线 （事务 + 批量插入 + 更新）
    Args:
        symbol: 股票代码，例如 "AAPL"、"000001.SZ"
        end_date: 截止日期，格式为 "YYYY-MM-DD"，默认为空，表示同步至最新数据
        count: 同步的天数，默认为1，表示同步最近的1个交易日数据
    """
    # 统计start_date到end_date的工作日数量
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    workdays = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:
            workdays += 1
        current += timedelta(days=1)

    # 获取股票日线数据
    stock_df = get_price(symbol, end_date=end_date, count=workdays)

    # 取所有日期键
    trade_dates = [
        (
            trade_date
            if isinstance(trade_date, datetime)
            else datetime.strptime(str(trade_date), "%Y-%m-%d").date()
        )
        for trade_date in stock_df.index
    ]

    async with in_transaction() as conn:
        # 查询数据库已有的 trade_date 列表（对应 stock_code）
        existing_records = (
            await DailyLine.filter(stock_code=symbol, trade_date__in=trade_dates)
            .using_db(conn)
            .all()
        )
        existing_dates = {record.trade_date for record in existing_records}

        new_records = []

        for trade_date, row in stock_df.iterrows():
            date_obj = (
                trade_date.date()
                if isinstance(trade_date, datetime)
                else datetime.strptime(str(trade_date), "%Y-%m-%d").date()
            )

            if date_obj not in existing_dates:

                # 新记录放入批量插入队列
                new_records.append(
                    DailyLine(
                        stock_code=symbol,
                        trade_date=date_obj,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=int(row["volume"]),
                        turnover=None,
                    )
                )

        # 批量插入新数据
        if new_records:
            await DailyLine.bulk_create(new_records, using_db=conn)
            logger.info(f"{symbol}数据获取成功")


class SyncService:

    @staticmethod
    async def get_config() -> SyncConfig:
        """获取单例配置记录"""
        config, _ = await SyncConfig.get_or_create(id=1)
        return config

    @classmethod
    async def get_summary(cls) -> Dict[str, Any]:
        """
        返回状态、计数和调度器信息
        """
        config = await cls.get_config()

        # 获取“最后一次同步时间”的最新完成日志
        last_log = (
            await SyncLog.filter(status=SyncStatus.SUCCESS)
            .order_by("-end_time")
            .first()
        )

        # 模拟数据统计在实际应用程序查询您的股票模型
        stock_count = await Stock.all().count()
        stat_days = 3350

        # 确定全局状态（检查当前是否有日志正在运行）
        running_task = await SyncLog.filter(status=SyncStatus.RUNNING).exists()
        current_status = "running" if running_task else "idle"

        last_sync_time = (
            int(last_log.end_time.timestamp() * 1000)
            if last_log and last_log.end_time
            else 0
        )

        return SyncSummaryResponse(
            last_sync_time=last_sync_time,
            data_range="2010-01-01 ~ 2025-11-28",
            stat_days=stat_days,
            stock_count=stock_count,
            scheduler={
                "enabled": config.scheduler_enabled,
                "time": config.scheduler_time,
            },
            status=current_status,
        )

    @classmethod
    async def get_logs(cls, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        获取同步日志
        """
        offset = (page - 1) * page_size

        total = await SyncLog.all().count()
        logs_query = await SyncLog.all().offset(offset).limit(page_size)

        # 将数据库模型转换为前端视图模型
        list_data = []
        for log in logs_query:
            list_data.append(
                {
                    "id": str(log.id),
                    "type": log.type,
                    "range": log.range_desc,
                    "startTime": log.start_time.isoformat(),  # Or custom format to match locale
                    "duration": log.duration(),
                    "status": log.status,
                }
            )

        return PaginatedData(
            list=list_data, total=total, page=page, page_size=page_size
        )

    @classmethod
    async def trigger_task(
        cls,
        type: str,
        data_range: List[str] | None = None,
        payload: Any = None,
    ) -> bool:
        """触发任务"""

        # 日期解析
        today = datetime.today()
        yesterday = today - timedelta(days=1)

        if not data_range:
            start_date = yesterday
            end_date = today if datetime.now().hour >= 16 else yesterday
        elif len(data_range) == 1:
            start_date = datetime.strptime(data_range[0], "%Y-%m-%d")
            end_date = today if datetime.now().hour >= 16 else yesterday
        else:
            start_date = datetime.strptime(data_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(data_range[1], "%Y-%m-%d")

        if await SyncLog.filter(status=SyncStatus.RUNNING).exists():
            raise Exception("A synchronization task is already in progress.")

        # 创建日志条目
        range_desc = (
            f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
        )

        if type == SyncType.BACKFILL:
            range_desc = "Custom Range Backfill"  # Parse payload for actual range

        log = await SyncLog.create(
            type=type, range_desc=range_desc, status=SyncStatus.RUNNING
        )

        try:
            stocks = [
                "000630.SZ",
                "000875.SZ",
                "002027.SZ",
                "002270.SZ",
                "002303.SZ",
                "002749.SZ",
                "002940.SZ",
                "300899.SZ",
                "301377.SZ",
                "301551.SZ",
                "600057.SH",
                "600908.SH",
            ]
            for stock in stocks:
                await sync_stock_daily_line(
                    stock, start_date=start_date, end_date=end_date
                )

            log.status = SyncStatus.SUCCESS
            logger.info(f"同步任务完成: {range_desc}")
            return True

        except Exception as e:
            log.status = SyncStatus.FAIL
            log.error_msg = str(e)
            logger.error(f"同步任务失败: {e}")
            return False

        finally:
            log.end_time = datetime.now()
            await log.save()

    @classmethod
    async def finish_task(cls, log_id: int, status: SyncStatus, error: str = None):
        """
        在同步完成时由后台工作线程调用
        """
        log = await SyncLog.get(id=log_id)
        log.end_time = datetime.now()
        log.status = status
        log.error_msg = error
        await log.save()
