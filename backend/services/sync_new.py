import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from tortoise.transactions import in_transaction
from tqdm.asyncio import tqdm

from backend.core.logger import logger
from backend.core.provider import get_price
from backend.enums.sync import SyncStatus, SyncType
from backend.models import DailyLine, Holiday, Stock, SyncConfig, SyncLog
from backend.schemas import PaginatedData, SyncSummaryResponse
from backend.utils import get_previous_trading_day


async def sync_stock_daily_line(start_date: datetime, end_date: datetime, symbols: List[str] | None = None):
    """
    批量同步日线数据
    Args:
        start_date: 开始日期
        end_date: 截止日期
        symbols: 股票代码列表
    """
    if symbols:
        stock_objs = await Stock.filter(full_stock_code__in=symbols).all()
    else:

        stock_objs = await Stock.filter(full_stock_code="600076.SH").all()
        # stock_objs = await Stock.all()
    symbols = [stock.full_stock_code for stock in stock_objs]

    logger.info(f"批量同步 {len(symbols)} 只股票的日线数据")
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # 交易天数统计
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

    # 一次性获取所有股票的数据
    all_data = {}
    for symbol in tqdm(symbols, desc="获取股票数据"):
        try:
            bars = get_price(symbol, end_date=end_date, count=trade_days)

            # 过滤数据：交易时间大于开始日期，跳过空数据
            bars = [bar for bar in bars if bar.trade_date >= start_date.date()]

            if not bars:
                continue

            all_data[symbol] = bars

            await asyncio.sleep(0.01)  # 避免获取频繁，导致服务异常

        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {e}")
            tqdm.write(f"获取 {symbol} 数据失败: {e}")

    if not all_data:
        logger.warning("未获取到任何股票数据")
        return
    logger.info(f"获取到 {len(all_data)} 条数据")

    # 一次性查询所有已存在的记录
    async with in_transaction() as conn:
        existing_records = (
            await DailyLine.filter(
                stock_code__in=symbols, trade_date__gte=start_date.date(), trade_date__lte=end_date.date()
            )
            .using_db(conn)
            .all()
        )

        # 构建 (stock_code, trade_date) 的集合，快速查询
        existing_set = {(record.stock_code, record.trade_date) for record in existing_records}
        new_records = []

        # 遍历所有股票数据，构建新记录列表
        for symbol, bars in all_data.items():
            for bar in bars:
                if (symbol, bar.trade_date) not in existing_set:
                    new_records.append(
                        DailyLine(
                            stock_code=symbol,
                            trade_date=bar.trade_date,
                            open=bar.open_,
                            high=bar.high,
                            low=bar.low,
                            close=bar.close,
                            volume=int(bar.volume),
                            turnover=None,
                        )
                    )

        # 一次性批量插入
        if new_records:
            await DailyLine.bulk_create(new_records, using_db=conn)
            logger.info(f"批量插入 {len(new_records)} 条记录成功")


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
        last_log = await SyncLog.filter(status=SyncStatus.SUCCESS).order_by("-end_time").first()

        # 模拟数据统计在实际应用程序查询您的股票模型
        stock_count = await Stock.all().count()
        stat_days = 3350

        # 确定全局状态（检查当前是否有日志正在运行）
        running_task = await SyncLog.filter(status=SyncStatus.RUNNING).exists()
        current_status = "running" if running_task else "idle"

        last_sync_time = int(last_log.end_time.timestamp() * 1000) if last_log and last_log.end_time else 0

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

        return PaginatedData(list=list_data, total=total, page=page, page_size=page_size)

    @classmethod
    async def trigger_task(
        cls,
        type: str,
        data_range: List[str] | None = None,
        payload: Any = None,
    ) -> bool:
        """触发任务"""

        # 日期解析
        logger.info("触发数据同步任务")
        today = datetime.today()
        previous_trading_day = datetime.strptime(await get_previous_trading_day(), "%Y-%m-%d")

        if not data_range:
            start_date = previous_trading_day
            end_date = today if datetime.now().hour >= 16 else previous_trading_day
        elif len(data_range) == 1:
            start_date = datetime.strptime(data_range[0], "%Y-%m-%d")
            end_date = today if datetime.now().hour >= 16 else previous_trading_day
        else:
            start_date = datetime.strptime(data_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(data_range[1], "%Y-%m-%d")

        if await SyncLog.filter(status=SyncStatus.RUNNING).exists():
            logger.warning("已有同步任务在运行中，跳过本次触发")
            raise Exception("A synchronization task is already in progress.")

        # 创建日志条目
        range_desc = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

        if type == SyncType.BACKFILL:
            range_desc = "Custom Range Backfill"  # Parse payload for actual range

        log = await SyncLog.create(type=type, range_desc=range_desc, status=SyncStatus.RUNNING)

        try:
            # 提取所有股票代码，一次性同步
            await sync_stock_daily_line(start_date=start_date, end_date=end_date)

            log.status = SyncStatus.SUCCESS
            logger.info(f"同步任务完成: {range_desc}")
            return True

        except Exception as e:
            import traceback

            log.status = SyncStatus.FAIL
            log.error_msg = str(e)
            logger.error(f"同步任务失败: {e}")
            logger.error(traceback.format_exc())  # 打印完整堆栈
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


sync_service = SyncService()
