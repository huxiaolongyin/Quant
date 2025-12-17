from datetime import datetime
from queue import Queue

import backtrader as bt

from backend.core.logger import logger
from backend.utils import send_email


class BaseStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        """日志记录函数"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f"{dt.isoformat()}, {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}"
                )
            else:
                self.log(
                    f"卖出执行, 价格: {order.executed.price:.2f}, 收益: {(self.size * order.executed.price - order.executed.value):.2f}, 手续费: {order.executed.comm:.2f}"
                )
                self.size = 0  # 卖出后清空持仓数量

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单被取消/拒绝")

        self.order = None
