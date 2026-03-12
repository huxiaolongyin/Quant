from backend.strategy_templates.schemas import (
    ParamType,
    StrategyCategory,
    StrategyParamDef,
    StrategyTemplate,
)
from backend.strategy_templates.registry import registry

BOLLINGER_TEMPLATE = StrategyTemplate(
    id="bollinger_strategy",
    name="布林带策略",
    description="使用布林带指标判断价格偏离。当价格触及下轨时买入，触及上轨时卖出。适用于震荡行情。",
    category=StrategyCategory.MEAN_REVERSION,
    tags=["布林带", "BOLL", "震荡", "均值回归"],
    params=[
        StrategyParamDef(
            name="period",
            display_name="计算周期",
            type=ParamType.INT,
            default=20,
            min=10,
            max=50,
            description="布林带计算周期，常用值为20",
        ),
        StrategyParamDef(
            name="dev_factor",
            display_name="标准差倍数",
            type=ParamType.FLOAT,
            default=2.0,
            min=1.0,
            max=3.0,
            description="布林带宽度标准差倍数，常用值为2",
        ),
    ],
    code='''import backtrader as bt

from backend.trading.strategies.base import BaseStrategy


class BollingerStrategy(BaseStrategy):
    """
    布林带策略：
    - 使用布林带指标判断价格偏离
    - 当价格触及下轨时买入
    - 当价格触及上轨时卖出
    """

    params = (
        ("period", 20),
        ("dev_factor", 2.0),
    )

    def __init__(self):
        self.size = 0
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.dev_factor,
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.data.close[0] <= self.boll.lines.bot[0]:
                cash = self.broker.getcash()
                available_cash = cash * 0.99
                price = self.data.close[0]
                self.size = int(available_cash / price) // 100 * 100
                if self.size > 0:
                    self.log(f"触及下轨买入, 价格: {price:.2f}, 下轨: {self.boll.lines.bot[0]:.2f}")
                    self.order = self.buy(size=self.size)
        else:
            if self.data.close[0] >= self.boll.lines.top[0]:
                self.size = self.position.size
                self.log(f"触及上轨卖出, 价格: {self.data.close[0]:.2f}, 上轨: {self.boll.lines.top[0]:.2f}")
                self.order = self.sell(size=self.size)
''',
    is_builtin=True,
)

registry.register(BOLLINGER_TEMPLATE)