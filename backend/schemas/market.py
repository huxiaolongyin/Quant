from decimal import Decimal
from typing import List, Optional

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
    sort_order: Optional[int] = Field(default=0, description="排序序号", examples=[1])
    notes: Optional[str] = Field(
        None, max_length=200, description="备注", examples=["长期持有"]
    )
    stock_code: Optional[str] = Field(
        None, max_length=200, description="股票代码", examples=["000001.SZ"]
    )
    short_name: Optional[str] = Field(
        None, max_length=200, description="股票名称", examples=["平安银行"]
    )


class WatchlistStockCreate(WatchlistStockBase):
    """创建自选股票"""

    stock_id: int = Field(..., description="股票ID", examples=[1])


class WatchlistStockUpdate(BaseSchema):
    """更新自选股票（所有字段可选）"""

    holding_num: Optional[int] = Field(None, ge=0, description="持有股数")
    cost_price: Optional[Decimal] = Field(
        None, ge=0, max_digits=10, decimal_places=3, description="成本价"
    )
    sort_order: Optional[int] = Field(None, description="排序序号")
    notes: Optional[str] = Field(None, max_length=200, description="备注")


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


class MinuteBar(BaseSchema):
    time: str
    open: float
    close: float
    high: float  # 建议添加
    low: float  # 建议添加
    volume: int


class StockQuote(BaseSchema):
    """实时行情响应"""

    code: str
    name: Optional[str] = None
    latest_price: float  # 最新价
    pre_close: float  # 昨收价
    change: float  # 涨跌额
    change_percent: float  # 涨跌幅 (%)
    open: float  # 今开
    high: float  # 最高
    low: float  # 最低
    volume: int  # 总成交量
    amount: Optional[float] = None  # 成交额
    price: float  # 持仓市值
    bars: List[MinuteBar]  # 分时明细

    class Config:
        from_attributes = True
