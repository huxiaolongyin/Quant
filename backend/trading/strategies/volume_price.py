import datetime

import backtrader as bt

from .base import BaseStrategy


class VolumePriceStrategy(BaseStrategy):
    """
    量价选股策略：
    - 天量天价：当成交量和股价同时达到过去N天的高点时，卖出信号
    - 地量低价：当成交量和股价同时达到过去N天的低点附近时，买入信号

    参数:
    - lookback: 用于计算最高/最低成交量和价格的回溯天数
    - vol_top_thresh: 天量判定阈值（成交量必须≥过去N天最大量 * 该比例）
    - vol_bottom_thresh: 地量判定阈值（成交量必须≤过去N天最小量 * 该比例）
    - price_top_thresh: 天价判定阈值（收盘价≥过去N天最高价 * 该比例）
    - price_bottom_thresh: 地价判定阈值（收盘价≤过去N天最低价 * 该比例）
    """

    params = (
        ("lookback", 20),
        ("vol_top_thresh", 0.9),
        ("vol_bottom_thresh", 1.1),  # 用1.1是因为是比例放大了比较方便比较
        ("price_top_thresh", 0.9),
        ("price_bottom_thresh", 1.1),
    )

    def __init__(self):
        self.size = 0
        self.order = None

        # 用linefromperiod类计算过去N天的最大成交量、最小成交量、最高价和最低价
        self.max_volume = bt.indicators.Highest(
            self.data.volume, period=self.params.lookback, subplot=False
        )
        self.min_volume = bt.indicators.Lowest(
            self.data.volume, period=self.params.lookback, subplot=False
        )
        self.max_price = bt.indicators.Highest(
            self.data.close, period=self.params.lookback, subplot=False
        )
        self.min_price = bt.indicators.Lowest(
            self.data.close, period=self.params.lookback, subplot=False
        )

    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return

        # 获取当前成交量和收盘价
        vol = self.data.volume[0]
        price = self.data.close[0]

        # 计算条件

        # 地量低价买入条件：
        # 当前volume ≤ min_volume * vol_bottom_thresh（这里阈值建议添加大于或等于判断）
        # 当前price ≤ min_price * price_bottom_thresh
        # 注意：这里设的vol_bottom_thresh和price_bottom_thresh > 1，表示允许价格和量在低点附近的一个溢出区间内
        buy_signal = (vol <= self.min_volume[0] * self.params.vol_bottom_thresh) and (
            price <= self.min_price[0] * self.params.price_bottom_thresh
        )

        # 天量天价卖出条件：
        # 当前volume ≥ max_volume * vol_top_thresh
        # 当前price ≥ max_price * price_top_thresh
        sell_signal = (vol >= self.max_volume[0] * self.params.vol_top_thresh) and (
            price >= self.max_price[0] * self.params.price_top_thresh
        )

        # 没有持仓，且满足买入信号，买入
        if not self.position and buy_signal:
            cash = self.broker.getcash()
            available_cash = cash * 0.99  # 预留手续费缓冲
            size = int(available_cash / price) // 100 * 100
            if size > 0:
                self.size = size
                self.log(f"买入信号，量：{vol}, 价:{price:.2f}，买入数量：{size}")
                self.order = self.buy(size=size)
            else:
                self.log(f"买入信号，量：{vol}, 价:{price:.2f}，资金不足买入")

        # 有持仓，且满足卖出信号，卖出全部
        elif self.position and sell_signal:
            self.size = self.position.size
            self.log(f"卖出信号，量：{vol}, 价:{price:.2f}，卖出数量：{self.size}")
            self.order = self.sell(size=self.size)
