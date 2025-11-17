import asyncio

import optuna

from core.stock_select import stock_select
from strategy.rsi import RSIStrategy
from strategy.volume_price import VolumePriceStrategy
from utils import run_backtest

# 目标股票池
# symbols = asyncio.run(stock_select())
symbols = ["000028.SZ"]


def objective(trial):
    # Optuna自动取样参数定义区间，示例为整数和浮点数参数
    try:
        rsi_period = trial.suggest_int("rsi_period", 10, 30)
        rsi_low = trial.suggest_int("rsi_low", 10, 40)
        rsi_high = trial.suggest_int("rsi_high", 60, 90)
        kwargs = {"rsi_period": rsi_period, "rsi_low": rsi_low, "rsi_high": rsi_high}

        results = []
        for symbol in symbols:
            # 封装的回测函数
            result = asyncio.run(
                run_backtest(symbol, RSIStrategy, "2025-01-01", **kwargs)
            )
            if result and len(result) > 4:
                results.append(result[4])
        if not results:
            return 0
        return sum(results) / len(results)
    except Exception as e:
        print("调用失败")
        return 0


# 回测主函数
if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)
    print("最佳参数:", study.best_params)
    print("最佳结果:", study.best_value)
