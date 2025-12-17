import datetime

import backtrader as bt


class MeanReversionStrategy(bt.Strategy):
    """
    简单均值回归策略：
    - 使用移动平均线作为"均值"
    - 当价格低于均值特定百分比时买入
    - 当价格高于均值特定百分比时卖出
    """

    params = (
        ("ma_period", 20),  # 移动平均线周期
        ("dev_factor", 2),  # 偏离因子（标准差的倍数）
        ("size", 200),  # 交易数量
    )

    def __init__(self):
        # 计算收盘价的简单移动平均线
        self.sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.ma_period
        )

        # 计算价格的标准差
        self.stddev = bt.indicators.StandardDeviation(
            self.data.close, period=self.params.ma_period
        )

        # 计算上下轨道线
        self.upper_band = self.sma + self.stddev * self.params.dev_factor
        self.lower_band = self.sma - self.stddev * self.params.dev_factor

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
            # 如果价格低于下轨，买入信号
            if self.data.close[0] < self.lower_band[0]:
                self.log(f"买入信号, 价格: {self.data.close[0]:.2f}")
                self.order = self.buy(size=self.params.size)
        else:
            # 如果价格高于上轨，卖出信号
            if self.data.close[0] > self.upper_band[0]:
                self.log(f"卖出信号, 价格: {self.data.close[0]:.2f}")
                self.order = self.sell(size=self.params.size)


if __name__ == "__main__":
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 加载数据
    from utils import get_stock_data

    stock_code = "300188.SZ"  # 示例股票代码
    start_date = "20230101"
    end_date = "20250715"
    stock_data = get_stock_data(stock_code, start_date, end_date)
    if not stock_data.empty:
        data = bt.feeds.PandasData(
            dataname=stock_data,
            fromdate=datetime.datetime.strptime(start_date, "%Y%m%d"),
            todate=datetime.datetime.strptime(end_date, "%Y%m%d"),
            name=stock_code,
        )
        cerebro.adddata(data)

        # 设置初始资金和佣金
        cerebro.broker.setcash(10000.0)
        cerebro.broker.setcommission(commission=0.0005)

        # 添加策略
        cerebro.addstrategy(MeanReversionStrategy)

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
