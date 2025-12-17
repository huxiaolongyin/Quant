import backtrader as bt

from backend.core.config import Settings
from backend.core.logger import logger
from backend.utils import date_process, format_code, get_stock_data


async def run_backtest(
    code: str,
    strategy: bt.Strategy,
    start_date: str,
    end_date: str = "",
    # is_plot: bool = False,
    init_cash: float = Settings.INIT_CACHE,
    **kwargs,
):
    """执行回测"""
    logger.info("-" * 75)
    logger.info(
        f"回测开始: 股票={code}, 策略={strategy.__qualname__}, 开始日期={start_date}, 参数={kwargs}"
    )
    # code = format_code(code)

    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 时间处理
    fromdate, todate = date_process(start_date, end_date)

    # 获取数据
    stock_data = await get_stock_data(code, fromdate, todate)

    data = bt.feeds.PandasData(
        dataname=stock_data,
        fromdate=fromdate,
        todate=todate,
        name=code,
    )
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(strategy, **kwargs)

    # 设置初始资金
    cerebro.broker.setcash(init_cash)

    # 设置佣金
    cerebro.broker.setcommission(commission=Settings.COMMISSION)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

    # 运行回测
    results = cerebro.run()
    strat = results[0]

    # 输出结果
    if cerebro.broker.getvalue() == init_cash:
        logger.warning("回测未产生交易，可能是数据或策略设置问题。")

        return init_cash, 0.0, 0.0  # 返回初始资金和收益率为0
    else:
        final_asset = round(cerebro.broker.getvalue(), 2)
        drawdown = strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]
        returns = strat.analyzers.returns.get_analysis()["rnorm100"]
        try:
            sharpe = round(strat.analyzers.sharpe.get_analysis()["sharperatio"], 3)
        except:
            sharpe = None

        logger.info(
            f"最终资产={final_asset}, 夏普比率={sharpe}, 最大回撤={drawdown:.2f}%, 年化收益率={returns:.2f}%"
        )

        # 绘制结果
        # if is_plot:
        #     cerebro.plot(style="candlestick")

        return (
            code,
            start_date,
            end_date,
            strategy.__name__,
            final_asset,
            f"{returns:.2f}%",
        )
