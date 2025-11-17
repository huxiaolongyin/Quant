from datetime import datetime

import backtrader as bt
import pandas as pd
from tortoise.expressions import Q

from core.init_app import with_db
from logger import get_logger
from models import DailyLine

logger = get_logger(__name__)


def get_stock_code(exchange_code=None, section="主板"):
    """
    获取A股股票代码列表
    """
    df = pd.read_csv("stocks.csv", sep=";")
    if exchange_code:
        df.query(f"交易所缩写 == '{exchange_code}'", inplace=True)
    df.query(f"板块 == '{section}'", inplace=True)

    return df["A股代码全称"].to_list()


# 数据获取与预处理函数
@with_db
async def _get_stock_data(
    stock_code: str, fromdate: datetime, todate: datetime
) -> pd.DataFrame:

    q = Q(stock_code=stock_code) & Q(trade_date__gt=fromdate)
    q &= Q(trade_date__lt=todate)

    stock_daily_data = await DailyLine.filter(q).all()

    df = pd.DataFrame([item.__dict__ for item in stock_daily_data])

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df.set_index("trade_date", inplace=True)

    # 数据预处理
    parse_df = df.copy()
    parse_df = parse_df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    parse_df = parse_df[["Open", "High", "Low", "Close", "Volume"]]

    parse_df.sort_index(ascending=True, inplace=True)

    return parse_df


async def run_backtest(
    stock_code: str,
    strategy: bt.Strategy,
    start_date: str,
    end_date: str = "",
    is_plot=False,
    init_cash=10000.0,
    **kwargs,
):
    if stock_code.endswith(".SZ"):
        stock_code = "sz" + stock_code[:6]
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    fromdate = datetime.strptime(start_date, "%Y-%m-%d")
    if not end_date:
        todate = datetime.today()
    else:
        todate = datetime.strptime(end_date, "%Y-%m-%d")

    # 获取数据
    stock_data = await _get_stock_data(stock_code, fromdate, todate)

    data = bt.feeds.PandasData(
        dataname=stock_data,
        fromdate=fromdate,
        todate=todate,
        name=stock_code,
    )
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(strategy, **kwargs)

    # 设置初始资金
    cerebro.broker.setcash(init_cash)

    # 设置佣金
    cerebro.broker.setcommission(commission=0.0005)  # 0.1%

    # 输出初始状态
    logger.info(
        f"股票: {stock_code} 开始回测。初始资金: {cerebro.broker.getvalue():.2f}"
    )

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

    # 运行回测
    # print("开始回测...")
    results = cerebro.run()
    strat = results[0]

    # 输出结果
    if cerebro.broker.getvalue() == init_cash:
        logger.warning("回测未产生交易，可能是数据或策略设置问题。")

        return 10000, 0.0, 0.0  # 返回初始资金和收益率为0
    else:
        logger.info(f"最终资产: {cerebro.broker.getvalue():.2f}")
        try:
            logger.info(
                f"夏普比率: {strat.analyzers.sharpe.get_analysis()['sharperatio']:.3f}"
            )
        except:
            logger.warning("夏普比率计算失败，可能是因为没有足够的数据。")
        logger.info(
            f"最大回撤: {strat.analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%"
        )
        logger.info(
            f"年化收益率: {strat.analyzers.returns.get_analysis()['rnorm100']:.2f}%"
        )
        logger.info("-" * 50)

        # 绘制结果
        if is_plot:
            cerebro.plot(style="candlestick")

        return (
            stock_code,
            start_date,
            end_date,
            strategy.__name__,
            round(cerebro.broker.getvalue(), 2),
            f'{round(strat.analyzers.returns.get_analysis()["rnorm100"],2)}%',
        )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(_get_stock_data("sh601212", start_date="2025-05-03")))
