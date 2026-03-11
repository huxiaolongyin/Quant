from datetime import datetime, timedelta

from tortoise import connections
from tortoise.expressions import Q

from backend.core.logger import logger
from backend.db.session import with_db
from backend.models import DailyLine, Stock
from backend.utils import get_previous_trading_day


@with_db
async def stock_select():
    """
    股票选取原则
    - 地区：深圳----经济特区，发展快
    - 排除 ST 股票----风险大
    - 最近单股股价<=50----钱少，买不起
    - 排除房地产、建筑业行业----行业不景气
    - 最近 30 天内，有3次或3次以上涨停或跌停的情况----水深，把握不住
    """
    yesterday_str = await get_previous_trading_day()
    start_date_str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    # 最近 30 天内，有3次或3次以上涨停或跌停的情况
    raw_sql = f"""
    -- stock_daily_line: 最近30天内，按“相邻收盘价涨跌幅”判断涨停/跌停次数>=3的股票
    WITH last_30d AS (
    SELECT *
    FROM stock_daily_line
    WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days'
    ),
    x AS (
    SELECT
        stock_code,
        trade_date,
        close,
        LAG(close) OVER (PARTITION BY stock_code ORDER BY trade_date) AS prev_close
    FROM last_30d
    ),
    limit_hits AS (
    SELECT
        stock_code,
        trade_date,
        CASE
        WHEN prev_close IS NULL OR prev_close = 0 THEN 0
        WHEN close >= prev_close * 1.099 THEN 1   -- 涨停：>= +9.9%
        WHEN close <= prev_close * 0.901 THEN 1   -- 跌停：<= -9.9%
        ELSE 0
        END AS is_limit_hit
    FROM x
    )
    SELECT
    stock_code,
    COUNT(*) FILTER (WHERE is_limit_hit = 1) AS limit_hit_cnt
    FROM limit_hits
    GROUP BY stock_code
    HAVING COUNT(*) FILTER (WHERE is_limit_hit = 1) >= 3
    ORDER BY limit_hit_cnt DESC, stock_code;
    """
    # 从 Tortoise 获取连接并执行
    conn = connections.get("default")
    result = await conn.execute_query_dict(raw_sql)
    limit_up_down_stocks = {row["stock_code"] for row in result}

    # 排除今天股价>50的
    today_lines = await DailyLine.filter(Q(trade_date=yesterday_str) & Q(close__lt=50)).all()

    # 股票列表
    stock_list = {
        line.stock_code
        for line in today_lines
        if line.stock_code not in limit_up_down_stocks
        and (line.stock_code.endswith(".SZ") or line.stock_code.endswith(".SH"))
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
    # print([stock.full_stock_code for stock in stocks])
    return [stock.full_stock_code for stock in stocks]


if __name__ == "__main__":
    import asyncio

    asyncio.run(stock_select())
