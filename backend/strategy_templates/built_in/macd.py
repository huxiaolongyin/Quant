from backend.strategy_templates.schemas import (
    ParamType,
    StrategyCategory,
    StrategyParamDef,
    StrategyTemplate,
)
from backend.strategy_templates.registry import registry

MACD_TEMPLATE = StrategyTemplate(
    id="macd_strategy",
    name="MACD策略",
    description="使用MACD指标的金叉和死叉作为买卖信号。当MACD线从下方穿过信号线时买入，从上方穿过时卖出。",
    category=StrategyCategory.TREND,
    tags=["MACD", "趋势", "经典指标", "金叉死叉"],
    params=[
        StrategyParamDef(
            name="fast_period",
            display_name="快线周期",
            type=ParamType.INT,
            default=12,
            min=5,
            max=30,
            description="MACD快线计算周期，常用值为12",
        ),
        StrategyParamDef(
            name="slow_period",
            display_name="慢线周期",
            type=ParamType.INT,
            default=26,
            min=15,
            max=50,
            description="MACD慢线计算周期，常用值为26",
        ),
        StrategyParamDef(
            name="signal_period",
            display_name="信号线周期",
            type=ParamType.INT,
            default=9,
            min=5,
            max=20,
            description="MACD信号线计算周期，常用值为9",
        ),
    ],
    code='''import backtrader as bt

from backend.trading.strategies.base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD策略：
    - 使用MACD指标的金叉和死叉作为买入和卖出信号
    - 当MACD线从下方穿过信号线时买入
    - 当MACD线从上方穿过信号线时卖出
    """

    params = (
        ("fast_period", 12),
        ("slow_period", 26),
        ("signal_period", 9),
    )

    def __init__(self):
        self.size = 0
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period,
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if (
                self.macd.macd[0] > self.macd.signal[0]
                and self.macd.macd[-1] < self.macd.signal[-1]
            ):
                cash = self.broker.getcash()
                available_cash = cash * 0.99
                price = self.data.close[0]
                self.size = int(available_cash / price) // 100 * 100
                if self.size > 0:
                    self.log(f"金叉买入, MACD: {self.macd.macd[0]:.2f}, 信号线: {self.macd.signal[0]:.2f}")
                    self.order = self.buy(size=self.size)
        else:
            if (
                self.macd.macd[0] < self.macd.signal[0]
                and self.macd.macd[-1] > self.macd.signal[-1]
            ):
                self.size = self.position.size
                self.log(f"死叉卖出, MACD: {self.macd.macd[0]:.2f}, 信号线: {self.macd.signal[0]:.2f}")
                self.order = self.sell(size=self.size)
''',
    is_builtin=True,
)

registry.register(MACD_TEMPLATE)