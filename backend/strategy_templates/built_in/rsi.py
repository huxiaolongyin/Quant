from backend.strategy_templates.schemas import (
    ParamType,
    StrategyCategory,
    StrategyParamDef,
    StrategyTemplate,
)
from backend.strategy_templates.registry import registry

RSI_TEMPLATE = StrategyTemplate(
    id="rsi_strategy",
    name="RSI策略",
    description="使用RSI指标判断超买超卖，当RSI低于阈值时买入，高于阈值时卖出。适用于震荡行情。",
    category=StrategyCategory.MEAN_REVERSION,
    tags=["RSI", "震荡", "经典指标", "均值回归"],
    params=[
        StrategyParamDef(
            name="rsi_period",
            display_name="RSI周期",
            type=ParamType.INT,
            default=14,
            min=5,
            max=50,
            description="RSI计算周期，常用值为14",
        ),
        StrategyParamDef(
            name="rsi_low",
            display_name="超卖阈值",
            type=ParamType.INT,
            default=30,
            min=10,
            max=40,
            description="RSI低于此值时触发买入信号",
        ),
        StrategyParamDef(
            name="rsi_high",
            display_name="超买阈值",
            type=ParamType.INT,
            default=70,
            min=60,
            max=90,
            description="RSI高于此值时触发卖出信号",
        ),
    ],
    code='''import backtrader as bt

from backend.trading.strategies.base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI策略：
    - 使用RSI作为买入和卖出信号
    - 当RSI低于超卖阈值时买入
    - 当RSI高于超买阈值时卖出
    """

    params = (
        ("rsi_period", 14),
        ("rsi_low", 30),
        ("rsi_high", 70),
    )

    def __init__(self):
        self.size = 0
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.params.rsi_low:
                cash = self.broker.getcash()
                available_cash = cash * 0.99
                price = self.data.close[0]
                self.size = int(available_cash / price) // 100 * 100
                if self.size > 0:
                    self.log(f"买入信号, RSI: {self.rsi[0]:.2f}, 价格: {price:.2f}, 数量: {self.size}")
                    self.order = self.buy(size=self.size)
                else:
                    self.log(f"买入信号, RSI: {self.rsi[0]:.2f}, 但资金不足")
        else:
            if self.rsi[0] > self.params.rsi_high:
                self.size = self.position.size
                self.log(f"卖出信号, RSI: {self.rsi[0]:.2f}, 卖出全部持仓: {self.size}股")
                self.order = self.sell(size=self.size)
''',
    is_builtin=True,
)

registry.register(RSI_TEMPLATE)