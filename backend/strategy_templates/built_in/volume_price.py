from backend.strategy_templates.schemas import (
    ParamType,
    StrategyCategory,
    StrategyParamDef,
    StrategyTemplate,
)
from backend.strategy_templates.registry import registry

VOLUME_PRICE_TEMPLATE = StrategyTemplate(
    id="volume_price_strategy",
    name="量价策略",
    description="结合成交量和价格判断买卖时机。地量低价时买入，天量天价时卖出。",
    category=StrategyCategory.VOLUME,
    tags=["量价", "成交量", "天量天价", "地量低价"],
    params=[
        StrategyParamDef(
            name="lookback",
            display_name="回溯周期",
            type=ParamType.INT,
            default=20,
            min=10,
            max=60,
            description="用于计算最高/最低成交量和价格的回溯天数",
        ),
        StrategyParamDef(
            name="vol_top_thresh",
            display_name="天量阈值",
            type=ParamType.FLOAT,
            default=0.9,
            min=0.8,
            max=1.0,
            description="成交量达到过去N天最大量的该比例时判定为天量",
        ),
        StrategyParamDef(
            name="vol_bottom_thresh",
            display_name="地量阈值",
            type=ParamType.FLOAT,
            default=1.1,
            min=1.0,
            max=1.5,
            description="成交量低于过去N天最小量乘以该比例时判定为地量",
        ),
        StrategyParamDef(
            name="price_top_thresh",
            display_name="天价阈值",
            type=ParamType.FLOAT,
            default=0.9,
            min=0.8,
            max=1.0,
            description="价格达到过去N天最高价的该比例时判定为天价",
        ),
        StrategyParamDef(
            name="price_bottom_thresh",
            display_name="地价阈值",
            type=ParamType.FLOAT,
            default=1.1,
            min=1.0,
            max=1.5,
            description="价格低于过去N天最低价乘以该比例时判定为地价",
        ),
    ],
    code='''import backtrader as bt

from backend.trading.strategies.base import BaseStrategy


class VolumePriceStrategy(BaseStrategy):
    """
    量价策略：
    - 天量天价：成交量和股价同时达到高点时卖出
    - 地量低价：成交量和股价同时达到低点附近时买入
    """

    params = (
        ("lookback", 20),
        ("vol_top_thresh", 0.9),
        ("vol_bottom_thresh", 1.1),
        ("price_top_thresh", 0.9),
        ("price_bottom_thresh", 1.1),
    )

    def __init__(self):
        self.size = 0
        self.order = None

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
        if self.order:
            return

        vol = self.data.volume[0]
        price = self.data.close[0]

        buy_signal = (
            vol <= self.min_volume[0] * self.params.vol_bottom_thresh
            and price <= self.min_price[0] * self.params.price_bottom_thresh
        )

        sell_signal = (
            vol >= self.max_volume[0] * self.params.vol_top_thresh
            and price >= self.max_price[0] * self.params.price_top_thresh
        )

        if not self.position and buy_signal:
            cash = self.broker.getcash()
            available_cash = cash * 0.99
            self.size = int(available_cash / price) // 100 * 100
            if self.size > 0:
                self.log(f"地量低价买入, 量: {vol}, 价: {price:.2f}, 数量: {self.size}")
                self.order = self.buy(size=self.size)
            else:
                self.log(f"地量低价买入信号, 但资金不足")

        elif self.position and sell_signal:
            self.size = self.position.size
            self.log(f"天量天价卖出, 量: {vol}, 价: {price:.2f}, 数量: {self.size}")
            self.order = self.sell(size=self.size)
''',
    is_builtin=True,
)

registry.register(VOLUME_PRICE_TEMPLATE)