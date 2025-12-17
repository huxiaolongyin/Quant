from decimal import Decimal
from typing import Optional

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
    sort_order: int = Field(default=0, description="排序序号", examples=[1])
    notes: Optional[str] = Field(
        None, max_length=200, description="备注", examples=["长期持有"]
    )
    stock_code: str = Field(
        max_length=200, description="股票代码", examples=["000001.SZ"]
    )
    short_name: str = Field(
        max_length=200, description="股票名称", examples=["平安银行"]
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
