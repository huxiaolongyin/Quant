"""自选股票 Service"""

from tortoise.transactions import atomic

from backend.models.market import WatchlistStock
from backend.schemas.market import WatchlistStockCreate, WatchlistStockUpdate

from .base import BaseService


class WatchlistStockService(
    BaseService[WatchlistStock, WatchlistStockCreate, WatchlistStockUpdate]
):
    """自选股票服务"""

    def __init__(self):
        super().__init__(WatchlistStock)

    async def get_list(self, *args, **kwargs):
        kwargs.setdefault("prefetch", [])
        if "stock" not in kwargs["prefetch"]:
            kwargs["prefetch"].append("stock")

        total, items = await super().get_list(*args, **kwargs)
        data = []
        for item in items:
            item_dict = await item.to_dict()
            # 从关联的 stock 获取字段
            if item.stock:
                item_dict["stock_code"] = item.stock.full_stock_code
                item_dict["short_name"] = item.stock.short_name
            data.append(item_dict)

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
