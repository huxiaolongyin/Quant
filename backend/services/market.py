"""自选股票 Service"""

from tortoise.transactions import atomic

from backend.models.market import WatchlistStock
from backend.schemas.market import (
    WatchlistStockCreate,
    WatchlistStockResponse,
    WatchlistStockUpdate,
)

from .base import BaseService


class WatchlistStockService(
    BaseService[WatchlistStock, WatchlistStockCreate, WatchlistStockUpdate]
):
    """自选股票服务"""

    def __init__(self):
        super().__init__(WatchlistStock)

    async def get_list(
        self, *args, **kwargs
    ) -> tuple[int, list[WatchlistStockResponse]]:
        kwargs.setdefault("prefetch", [])
        if "stock" not in kwargs["prefetch"]:
            kwargs["prefetch"].append("stock")

        total, items = await super().get_list(*args, **kwargs)

        # 使用Pydantic模型序列化
        data = []
        for item in items:
            item_data = {
                **item.__dict__,
                "stock_code": item.stock.full_stock_code if item.stock else None,
                "short_name": item.stock.short_name if item.stock else None,
            }
            data.append(WatchlistStockResponse.model_validate(item_data))

        return total, data

    async def is_stock_in_watchlist(self, stock_id: int) -> bool:
        """检查股票是否已在自选中"""
        return await self.model.filter(stock_id=stock_id).exists()

    @atomic()
    async def reorder(self, items: list[dict[str, int]]) -> int:
        """
        批量更新排序

        Args:
            items: [{"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1}]

        Returns:
            更新数量
        """
        updated = 0
        for item in items:
            count = await self.model.filter(id=item["id"]).update(
                sort_order=item["sort_order"]
            )
            updated += count
        return updated


# 单例
watchlist_stock_service = WatchlistStockService()
