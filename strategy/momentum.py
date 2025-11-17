import math

import backtrader as bt
import numpy as np

"""
通过计算 stock 的动量得分来选择股票进行投资。
得分计算：周期内的年化收益率 * R²，连续3日跌幅超过5%的股票得分为0。
每20个交易日调仓一次，选择1个或2个最高的股票进行买入，其他卖出。

"""


class MomentumStrategy(bt.Strategy):
    params = (
        ("short_period", 25),  # 短期动量周期
        ("long_period", 250),  # 长期动量周期
        ("max_short_score", 6),  # 短期最大得分
        ("max_long_score", 0.5),  # 长期最大得分
        ("rebalance_days", 20),  # 调仓周期(交易日)
    )

    def log(self, txt, dt=None):
        """日志函数"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def __init__(self):
        # 跟踪天数
        self.day_count = 0

        # 创建stock代码到数据的映射
        self.stock_dict = {}
        for i, d in enumerate(self.datas):
            self.stock_dict[d._name] = i

        # 当前持仓
        self.current_positions = {}

        # 挂单跟踪
        self.orders = {}
        for d in self.datas:
            self.orders[d] = None

    def calculate_score(self, data, period):
        """
        计算stock的动量得分
        """
        # 获取收盘价和最高价
        prices = np.array([data.close.get(i, size=1)[0] for i in range(-period, 0)])

        # 设置参数
        y = np.log(prices)
        x = np.arange(len(y))
        weights = np.linspace(1, 2, len(y))

        # 计算年化收益率
        slope, intercept = np.polyfit(x, y, 1, w=weights)
        annualized_returns = math.exp(slope * 250) - 1

        # 计算R²
        ss_res = np.sum(weights * (y - (slope * x + intercept)) ** 2)
        ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot else 0

        # 计算得分
        score = annualized_returns * r2

        # 过滤近3日跌幅超过5%的stock
        if (
            max(
                prices[-1] / prices[-2],
                prices[-2] / prices[-3],
                prices[-3] / prices[-4],
            )
            < 0.95,
        ):
            print(f"过滤 {data._name}，近3日跌幅超过5%")
            score = 0

        return score

    def filter_stocks(self, max_score, period):
        """根据动量和R²过滤tocks"""
        scores = {}

        for stock_code, idx in self.stock_dict.items():
            data = self.datas[idx]

            # 确保有足够的数据
            if len(data) < period:
                continue

            score = self.calculate_score(data, period)

            # 过滤得分
            if 0 < score < max_score:
                scores[stock_code] = score

        # 如果没有符合条件的stock，返回默认的
        if not scores:
            return "002555.SZ"  # 30年国债stock作为默认

        # 返回得分最高的stock
        return max(scores.items(), key=lambda x: x[1])[0]

    def select_stocks(self):
        """选择stock"""
        # 短期动量选股
        stock1 = self.filter_stocks(self.p.max_short_score, self.p.short_period)

        # 长期动量选股
        stock2 = self.filter_stocks(self.p.max_long_score, self.p.long_period)

        return [stock1, stock2] if stock1 != stock2 else [stock1]

    def notify_order(self, order):
        """订单状态更新通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入 {order.data._name} 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}"
                )
            else:
                self.log(
                    f"卖出 {order.data._name} 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"订单被取消/拒绝/保证金不足: {order.data._name}")

        # 清除订单引用
        self.orders[order.data] = None

    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return

        self.log(f"交易利润: 总计 {trade.pnl:.2f}, 净值 {trade.pnlcomm:.2f}")

    def next(self):
        """下一个交易日"""
        self.day_count += 1

        # 每20个交易日调仓一次
        if self.day_count % self.p.rebalance_days != 0:
            return

        # 获取当前持仓
        current_positions = {}
        for data in self.datas:
            position = self.getposition(data).size
            if position:
                current_positions[data._name] = position

        # 记录调仓日
        self.log(
            f"执行调仓, 当前资产: {self.broker.getvalue():.2f}, 持仓: {current_positions}"
        )

        # 选出要持有的stock
        selected_stocks = self.select_stocks()
        self.log(f"选出的stock: {selected_stocks}")

        # 计算每个stock应该分配的资金比例
        target_percent = 1.0 / len(selected_stocks)

        # 卖出不在目标组合中的stock
        for stock_code, idx in self.stock_dict.items():
            data = self.datas[idx]

            # 如果有挂单，跳过
            if self.orders[data]:
                continue

            # 如果该stock不在目标组合中且有持仓，则全部卖出
            if stock_code not in selected_stocks and self.getposition(data).size > 0:
                self.log(f"卖出 {stock_code}")
                self.orders[data] = self.close(data)

        # 买入或调整目标组合中的stock
        for stock_code in selected_stocks:
            if stock_code not in self.stock_dict:
                self.log(f"stock {stock_code} 不在数据集中，跳过")
                continue

            data = self.datas[self.stock_dict[stock_code]]

            # 如果有挂单，跳过
            if self.orders[data]:
                continue

            # 计算目标持仓金额
            target_value = self.broker.getvalue() * target_percent

            # 计算当前持仓价值
            current_value = self.getposition(data).size * data.close[0]

            # 如果需要调整
            if abs(target_value - current_value) > 0.05 * target_value:  # 5%的阈值
                if target_value > current_value:
                    # 需要买入
                    size = int((target_value - current_value) / data.close[0])

                    # 添加交易规则限制
                    # 1. 确保股数是100的整数倍（一手为单位）
                    size = (size // 100) * 100

                    # 2. 限制单次交易最大股数
                    max_shares = 2000  # 设置合理的最大交易股数
                    if size > max_shares:
                        size = max_shares
                        self.log(f"限制 {stock_code} 买入数量为 {size} 股")

                    # 3. 检查是否有足够的资金
                    cost = size * data.close[0]
                    if cost > self.broker.getcash() * 0.95:  # 留5%作为缓冲
                        size = int((self.broker.getcash() * 0.95) / data.close[0])
                        size = (size // 100) * 100  # 确保是100的整数倍
                        self.log(f"资金限制，调整 {stock_code} 买入数量为 {size} 股")

                    if size >= 100:  # 至少买一手
                        self.log(f"买入 {stock_code}, 数量: {size}")
                        self.orders[data] = self.buy(data, size=size)
                    else:
                        self.log(f"买入 {stock_code} {size}股，数量不足一手，跳过")
                else:
                    # 需要卖出
                    size = int((current_value - target_value) / data.close[0])
                    if size > 0:
                        self.log(f"部分卖出 {stock_code}, 数量: {size}")
                        self.orders[data] = self.sell(data, size=size)
