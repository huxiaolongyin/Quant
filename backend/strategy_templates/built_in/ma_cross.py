from backend.strategy_templates.schemas import (
    ParamType,
    StrategyCategory,
    StrategyParamDef,
    StrategyTemplate,
)
from backend.strategy_templates.registry import registry

MA_CROSS_TEMPLATE = StrategyTemplate(
    id="ma_cross_strategy",
    name="双均线策略",
    description="使用短期和长期移动平均线的交叉作为买卖信号。短期均线上穿长期均线时买入，下穿时卖出。",
    category=StrategyCategory.TREND,
    tags=["均线", "趋势", "MA", "金叉死叉"],
    params=[
        StrategyParamDef(
            name="short_period",
            display_name="短期均线周期",
            type=ParamType.INT,
            default=5,
            min=3,
            max=20,
            description="短期移动平均线周期，常用值为5或10",
        ),
        StrategyParamDef(
            name="long_period",
            display_name="长期均线周期",
            type=ParamType.INT,
            default=20,
            min=10,
            max=60,
            description="长期移动平均线周期，常用值为20或60",
        ),
    ],
    code='''import backtrader as bt

from backend.trading.strategies.base import BaseStrategy


class MACrossStrategy(BaseStrategy):
    """
    双均线策略：
    - 使用短期和长期移动平均线的交叉作为买卖信号
    - 短期均线上穿长期均线时买入（金叉）
    - 短期均线下穿长期均线时卖出（死叉）
    """

    params = (
        ("short_period", 5),
        ("long_period", 20),
    )

    def __init__(self):
        self.size = 0
        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.short_ma[0] > self.long_ma[0] and self.short_ma[-1] <= self.long_ma[-1]:
                cash = self.broker.getcash()
                available_cash = cash * 0.99
                price = self.data.close[0]
                self.size = int(available_cash / price) // 100 * 100
                if self.size > 0:
                    self.log(f"金叉买入, 短期MA: {self.short_ma[0]:.2f}, 长期MA: {self.long_ma[0]:.2f}")
                    self.order = self.buy(size=self.size)
        else:
            if self.short_ma[0] < self.long_ma[0] and self.short_ma[-1] >= self.long_ma[-1]:
                self.size = self.position.size
                self.log(f"死叉卖出, 短期MA: {self.short_ma[0]:.2f}, 长期MA: {self.long_ma[0]:.2f}")
                self.order = self.sell(size=self.size)
''',
    is_builtin=True,
)

registry.register(MA_CROSS_TEMPLATE)