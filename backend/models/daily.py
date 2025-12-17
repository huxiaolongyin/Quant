from tortoise import fields, models

from .base import BaseModel


class DailyLine(BaseModel):
    """历史日线数据模型"""

    id = fields.IntField(pk=True)  # 主键
    stock_code = fields.CharField(max_length=20, description="股票代码或标的符号")
    trade_date = fields.DateField(description="交易日期")
    open = fields.DecimalField(max_digits=10, decimal_places=4, description="开盘价")
    high = fields.DecimalField(max_digits=10, decimal_places=4, description="最高价")
    low = fields.DecimalField(max_digits=10, decimal_places=4, description="最低价")
    close = fields.DecimalField(max_digits=10, decimal_places=4, description="收盘价")
    volume = fields.BigIntField(description="成交量")
    turnover = fields.DecimalField(
        max_digits=20, decimal_places=2, null=True, description="成交额（可选）"
    )

    class Meta:
        table = "stock_daily_line"
        unique_together = ("stock_code", "trade_date")
        ordering = ["-trade_date"]

    def __str__(self):
        return f"股票={self.stock_code}, 日期={self.trade_date}, 开盘价={self.open}, 最高价={self.high}, 最低价={self.low}, 收盘价={self.close}"
