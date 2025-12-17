import datetime

import backtrader as bt
import pandas as pd


class MACDStrategy(bt.Strategy):
    """
    MACD策略：
    - 使用MACD指标的金叉和死叉作为买入和卖出信号
    - 当MACD线从下方穿过信号线时买入
    - 当MACD线从上方穿过信号线时卖出
    """

    params = (
        ("macd_period", 12),  # MACD短期周期
        ("signal_period", 26),  # MACD长期周期
        ("signal_smoothing", 9),  # 信号线周期
        ("size", 100),  # 交易数量
    )

    def __init__(self):
        # 计算MACD指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_period,
            period_me2=self.params.signal_period,
            period_signal=self.params.signal_smoothing,
        )

        # 跟踪订单
        self.order = None

    def log(self, txt, dt=None):
        """日志记录函数"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}"
                )
            else:
                self.log(
                    f"卖出执行, 价格: {order.executed.price:.2f}, 收益: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单被取消/拒绝")

        self.order = None

    def next(self):
        # 如果有未完成的订单，直接返回
        if self.order:
            return

        # 检查是否已有持仓
        if not self.position:
            # 如果出现金叉，买入信号
            if (
                self.macd.macd[0] > self.macd.signal[0]
                and self.macd.macd[-1] < self.macd.signal[-1]
            ):
                self.log(
                    f"买入信号, MACD: {self.macd.macd[0]:.2f}, 信号线: {self.macd.signal[0]:.2f}"
                )
                self.order = self.buy(size=self.params.size)
        else:
            # 如果出现死叉，卖出信号
            if (
                self.macd.macd[0] < self.macd.signal[0]
                and self.macd.macd[-1] > self.macd.signal[-1]
            ):
                self.log(
                    f"卖出信号, MACD: {self.macd.macd[0]:.2f}, 信号线: {self.macd.signal[0]:.2f}"
                )
                self.order = self.sell(size=self.params.size)


# 回测主函数
def run_backtest():
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 加载数据
    from utils import get_stock_data

    stock_code = "300209.SZ"  # 示例股票代码
    start_date = "20240701"
    end_date = "20250728"
    stock_data = get_stock_data(stock_code, start_date, end_date)
    data = bt.feeds.PandasData(
        dataname=stock_data,
        fromdate=datetime.datetime.strptime(start_date, "%Y%m%d"),
        todate=datetime.datetime.strptime(end_date, "%Y%m%d"),
        name=stock_code,
    )
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(MACDStrategy)

    # 设置初始资金
    cerebro.broker.setcash(10000.0)

    # 设置佣金
    cerebro.broker.setcommission(commission=0.001)  # 0.1%

    # 输出初始状态
    print(f"初始资金: {cerebro.broker.getvalue():.2f}")

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

    # 运行回测
    print("开始回测...")
    results = cerebro.run()
    strat = results[0]

    # 输出结果
    print(f"最终资产: {cerebro.broker.getvalue():.2f}")
    print(f"夏普比率: {strat.analyzers.sharpe.get_analysis()['sharperatio']:.3f}")
    print(
        f"最大回撤: {strat.analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%"
    )
    print(f"年化收益率: {strat.analyzers.returns.get_analysis()['rnorm100']:.2f}%")

    # 绘制结果
    cerebro.plot(style="candlestick")


if __name__ == "__main__":
    run_backtest()
