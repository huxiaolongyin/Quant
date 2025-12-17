from datetime import datetime, timedelta

from tortoise import connections
from tortoise.expressions import Q

from backend.core.logger import logger
from backend.db.session import with_db
from backend.models import DailyLine, Stock
from backend.utils import get_previous_workday


@with_db
async def stock_select():
    """
    股票选取原则
    - 地区：深圳----经济特区，发展快
    - 排除 ST 股票----风险大
    - 最近单股股价<=50----钱少，买不起
    - 排除房地产、建筑业行业----行业不景气
    - 最近 15 天内，有涨停或跌停的情况----水深，把握不住
    """

    yesterday_str = get_previous_workday()
    start_date_str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    # 找出最近15天的涨停股
    raw_sql = f"""
    WITH daily_with_pre_close AS (
    SELECT
        stock_code,
        close,
        LAG(close, 1) OVER (PARTITION BY stock_code ORDER BY trade_date) AS pre_close
    FROM
        stock_daily_line
    WHERE
        trade_date  >= '{start_date_str}'
    )
    SELECT
        stock_code
    FROM (
        SELECT
            stock_code, count(1) as total
        FROM daily_with_pre_close
        WHERE
            pre_close IS NOT NULL
            AND (close >= ROUND(pre_close * 1.099, 2) OR close <= ROUND(pre_close * 0.901, 2))
        GROUP BY stock_code
        )   
    WHERE total>=2
    """
    # 从 Tortoise 获取连接并执行
    conn = connections.get("default")
    result = await conn.execute_query_dict(raw_sql)
    limit_up_down_stocks = {row["stock_code"] for row in result}

    # 排除今天股价>50的
    today_lines = await DailyLine.filter(
        Q(trade_date=yesterday_str) & Q(close__lt=50)
    ).all()

    # 股票列表
    stock_list = {
        line.stock_code
        for line in today_lines
        if line.stock_code not in limit_up_down_stocks
        and line.stock_code.endswith(".SZ")
    }

    q = (
        Q(city="深圳市")
        & Q(full_stock_code__in=stock_list)
        & Q(sector="主板")
        & ~Q(short_name__icontains="ST")
        & ~Q(industry__in=["K 房地产", "E 建筑业"])
    )
    stocks = await Stock.filter(q).all()
    logger.info(f"股票池: {len(stocks)}")
    return [stock.full_stock_code for stock in stocks]


if __name__ == "__main__":
    import asyncio

    asyncio.run(stock_select())
