from datetime import date
from decimal import Decimal
from typing import List

from pydantic import Field

from .base import BaseSchema, IDMixin, TimestampMixin


class WatchlistStockBase(BaseSchema):
    """自选股票基础字段"""

    holding_num: int = Field(default=0, ge=0, description="持有股数", examples=[100])
    cost_price: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=10,
        decimal_places=3,
        description="成本价",
        examples=["15.500"],
    )
    sort_order: int | None = Field(default=0, description="排序序号", examples=[1])
    notes: str | None = Field(
        None, max_length=200, description="备注", examples=["长期持有"]
    )
    stock_code: str | None = Field(
        None, max_length=200, description="股票代码", examples=["000001.SZ"]
    )
    short_name: str | None = Field(
        None, max_length=200, description="股票名称", examples=["平安银行"]
    )


class WatchlistStockCreate(WatchlistStockBase):
    """创建自选股票"""

    stock_id: int = Field(..., description="股票ID", examples=[1])


class WatchlistStockUpdate(BaseSchema):
    """更新自选股票（所有字段可选）"""

    holding_num: int | None = Field(None, ge=0, description="持有股数")
    cost_price: Decimal | None = Field(
        None, ge=0, max_digits=10, decimal_places=3, description="成本价"
    )
    sort_order: int | None = Field(None, description="排序序号")
    notes: str | None = Field(None, max_length=200, description="备注")


class WatchlistStockReorder(BaseSchema):
    """调整排序"""

    items: list[dict[str, int]] = Field(
        ...,
        description="排序项列表",
        examples=[[{"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1}]],
    )


class WatchlistStockResponse(WatchlistStockBase, IDMixin, TimestampMixin):
    """自选股票响应"""

    ...


class StockBase(BaseSchema):
    """股票交易基础"""

    open: float
    close: float
    high: float
    low: float
    volume: int


class MinuteBar(StockBase):
    """分钟级股票明细"""

    time: str


class DateBar(StockBase):
    """日级股票行情数据"""

    stock_code: str
    trade_date: date
    turnover: float | None


class StockQuote(BaseSchema):
    """实时行情响应"""

    code: str
    name: str | None = None
    latest_price: float  # 最新价
    pre_close: float  # 昨收价
    change: float  # 涨跌额
    change_percent: float  # 涨跌幅 (%)
    open: float  # 今开
    high: float  # 最高
    low: float  # 最低
    volume: int  # 总成交量
    amount: float | None = None  # 成交额
    holding_num: float  # 持仓数
    market_value: float  # 持仓市值
    pre_market_value: float  # 昨日持仓市值
    bars: List[MinuteBar]  # 分时明细

    class Config:
        from_attributes = True
