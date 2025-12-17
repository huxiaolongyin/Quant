import asyncio

import optuna

from backend.core.logger import logger
from backend.core.selector import stock_select
from backend.trading.engine import run_backtest
from backend.trading.strategies.rsi import RSIStrategy
from backend.trading.strategies.volume_price import VolumePriceStrategy

# 目标股票池
symbols = asyncio.run(stock_select())
# symbols = ["002106.SZ"]


def objective(trial):
    """Optuna自动取样参数定义区间，示例为整数和浮点数参数"""

    rsi_period = trial.suggest_int("rsi_period", 10, 30)
    rsi_low = trial.suggest_int("rsi_low", 10, 40)
    rsi_high = trial.suggest_int("rsi_high", 60, 90)
    kwargs = {"rsi_period": rsi_period, "rsi_low": rsi_low, "rsi_high": rsi_high}
    start_date = "2025-01-01"

    results = []
    for symbol in symbols:
        result = asyncio.run(run_backtest(symbol, RSIStrategy, start_date, **kwargs))
        if result and len(result) > 4:
            results.append(result[4])
    if not results:
        return 0
    return sum(results) / len(results)


def train():
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=1)
    logger.info(f"最佳参数={study.best_params}, 平均资产={study.best_value:.2f}")


def execute():
    """执行"""
    start_date = "2024-01-01"
    kwargs = {"rsi_period": 14, "rsi_low": 25, "rsi_high": 75}
    for symbol in symbols:
        result = asyncio.run(run_backtest(symbol, RSIStrategy, start_date, **kwargs))


# 回测主函数
if __name__ == "__main__":
    execute()
