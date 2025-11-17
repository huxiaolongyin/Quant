import datetime

import backtrader as bt

from strategy.base import BaseStrategy
from utils import send_email


class RSIStrategy(BaseStrategy):
    """
    RSI策略：
    - 使用RSI作为买入和卖出信号
    - 当RSI低于30时买入
    - 当RSI高于70时卖出
    """

    params = (
        ("rsi_period", 14),  # RSI周期
        ("rsi_low", 30),  # RSI超卖阈值
        ("rsi_high", 70),  # RSI超买阈值
    )

    def __init__(self):
        self.size = 0  # 初始化持仓数量

        # 计算RSI指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

        # 跟踪订单
        self.order = None

    def next(self):
        dt = self.datas[0].datetime.date(0)
        close = self.datas[0].close[0]
        trade_signal = dt == datetime.datetime.today().date()
        # 如果有未完成的订单，直接返回
        if self.order:
            return

        # 检查是否已有持仓
        if not self.position:

            # 如果RSI低于超卖阈值，买入信号
            if self.rsi[0] < self.params.rsi_low:

                # 获取当前可用资金
                cash = self.broker.getcash()

                # 预留1%的资金作为手续费缓冲
                available_cash = cash * 0.99

                # 计算可以购买的股票数量
                price = self.data.close[0]

                # 计算股数并确保整百
                self.size = int(available_cash / price) // 100 * 100
                if self.size > 0:
                    self.log(
                        f"买入信号, RSI: {self.rsi[0]:.2f}, 价格: {price:.2f}, 数量: {self.size}"
                    )
                    if trade_signal:
                        subject = f"{dt}股票量化买入信号: {self.datas[0]._name}"
                        content = f"""
                        信号: BUY
                        日期: {dt}
                        收盘价格: {close:.2f}
                        策略 {self.__class__.__name__}
                        """
                        send_email(subject, content)
                    self.order = self.buy(size=self.size)
                else:

                    self.log(f"买入信号, RSI: {self.rsi[0]:.2f}, 但资金不足")
        else:
            # 如果RSI高于超买阈值，卖出信号
            if self.rsi[0] > self.params.rsi_high:
                # 获取当前持仓数量
                self.size = self.position.size
                self.log(
                    f"卖出信号, RSI: {self.rsi[0]:.2f}， 卖出全部持仓: {self.size}股"
                )
                if trade_signal:
                    subject = f"{dt}股票量化卖出信号: {self.datas[0]._name}"
                    content = f"""
                    信号: SELL
                    日期: {dt}
                    收盘价格: {close:.2f}
                    策略 {self.__class__.__name__}
                    """
                    send_email(subject, content)
                self.order = self.sell(size=self.size)
