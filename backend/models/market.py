"""自选股票 ORM 模型"""

from tortoise import fields

from .base import BaseModel


class WatchlistStock(BaseModel):
    """自选股票"""

    id = fields.IntField(pk=True)
    stock = fields.ForeignKeyField(
        "quant.Stock", related_name="selected_by", on_delete=fields.RESTRICT
    )
    holding_num = fields.IntField(default=0, description="持有股数")
    cost_price = fields.FloatField(default=0.0, description="成本价")
    sort_order = fields.IntField(default=0, description="排序序号")
    notes = fields.CharField(max_length=200, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "watchlist_stocks"
        ordering = ["sort_order", "-created_at"]
        unique_together = [("stock",)]

    def __str__(self):
        return f"Watchlist(stock_id={self.stock_id}, holding={self.holding_num})"
