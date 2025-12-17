from datetime import datetime

import pandas as pd
from tortoise.transactions import in_transaction

from backend.core.logger import logger
from backend.core.provider import get_price
from backend.db.session import with_db
from backend.models import DailyLine, Stock


async def sync_stock(csv_path: str):
    "同步股票列表，读取csv，写入数据库"

    # 使用 pandas 读取 CSV
    df = pd.read_csv(csv_path, sep=";")

    # 简单检查列表
    expected_columns = [
        "交易所名称",
        "交易所缩写",
        "板块",
        "A股代码",
        "A股代码全称",
        "A股简称",
        "英文名称",
        "公司全称",
        "A股上市日期",
        "所属行业",
        "省份",
        "城市",
    ]

    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"缺少关键列: {missing_columns}")

    # 事务写入数据库
    async with in_transaction() as connection:
        for _, row in df.iterrows():
            # 将日期转换为 python 日期类型，如果有空可适当处理
            listing_date = row.get("A股上市日期")
            if pd.isna(listing_date):
                listing_date = None
            else:
                listing_date = pd.to_datetime(listing_date).date()

            # 利用a_share_code唯一定位，存在则更新，不存在则创建
            stock_obj = (
                await Stock.filter(stock_code=row["A股代码"])
                .using_db(connection)
                .first()
            )
            if stock_obj:
                stock_obj.exchange_name = row["交易所名称"]
                stock_obj.exchange_code = row["交易所缩写"]
                stock_obj.sector = row["板块"]
                stock_obj.short_name = row["A股简称"]
                stock_obj.english_name = (
                    row["英文名称"] if not pd.isna(row["英文名称"]) else None
                )
                stock_obj.company_full_name = row["公司全称"]
                stock_obj.listing_date = listing_date
                stock_obj.industry = (
                    row["所属行业"] if not pd.isna(row["所属行业"]) else None
                )
                stock_obj.province = row["省份"] if not pd.isna(row["省份"]) else None
                stock_obj.city = row["城市"] if not pd.isna(row["城市"]) else None

                await stock_obj.save(using_db=connection)
            else:
                await Stock.create(
                    exchange_name=row["交易所名称"],
                    exchange_code=row["交易所缩写"],
                    sector=row["板块"],
                    stock_code=row["A股代码"],
                    full_stock_code=row["A股代码全称"],
                    short_name=row["A股简称"],
                    english_name=(
                        row["英文名称"] if not pd.isna(row["英文名称"]) else None
                    ),
                    company_full_name=row["公司全称"],
                    listing_date=listing_date,
                    industry=(
                        row["所属行业"] if not pd.isna(row["所属行业"]) else None
                    ),
                    province=row["省份"] if not pd.isna(row["省份"]) else None,
                    city=row["城市"] if not pd.isna(row["城市"]) else None,
                    using_db=connection,
                )


async def sync_stock_daily_line(symbol: str, end_date: str = "", count: int = 1):
    """
    同步日线 （事务 + 批量插入 + 更新）
    Args:
        symbol: 股票代码，例如 "AAPL"、"000001.SZ"
        end_date: 截止日期，格式为 "YYYY-MM-DD"，默认为空，表示同步至最新数据
        count: 同步的天数，默认为1，表示同步最近的1个交易日数据
    """

    stock_df = get_price(symbol, end_date=end_date, count=count)

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


@with_db
async def main():
    # stocks = [
    #     "000630.SZ",
    #     "000875.SZ",
    #     "002027.SZ",
    #     "002270.SZ",
    #     "002303.SZ",
    #     "002749.SZ",
    #     "002940.SZ",
    #     "300899.SZ",
    #     "301377.SZ",
    #     "301551.SZ",
    #     "600057.SH",
    #     "600908.SH",
    # ]
    # for stock in stocks:
    #     await sync_stock_daily_line(stock, count=1)
    #     await asyncio.sleep(0.5)
    # from tortoise.expressions import Q

    stock_objs = await Stock.all()

    for stock in stock_objs:

        await sync_stock_daily_line(stock.full_stock_code, count=1)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
