from typing import List, Optional, Tuple

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from backend.models.strategy import (
    Strategy,
    StrategyBacktest,
    StrategyPerformance,
    StrategyTag,
    StrategyTagRelation,
)
from backend.schemas.strategy import (
    StrategyCreateSchema,
    StrategyListParams,
    StrategyTagCreateSchema,
    StrategyUpdateSchema,
)
from backend.services.base import BaseService


class StrategyService(
    BaseService[Strategy, StrategyCreateSchema, StrategyUpdateSchema]
):
    """策略服务"""

    def __init__(self):
        super().__init__(Strategy)

    async def get_list_with_performance(
        self, params: StrategyListParams
    ) -> Tuple[int, List[dict]]:
        """获取策略列表（包含绩效数据和标签）"""

        # 构建查询条件
        search_q = Q()

        # 搜索条件
        if params.search:
            search_q &= Q(name__icontains=params.search)

        # 状态筛选
        if params.status:
            search_q &= Q(status=params.status)

        # 创建者筛选
        if params.created_by:
            search_q &= Q(created_by=params.created_by)

        # 标签筛选
        if params.tag_id:
            search_q &= Q(tag_relations__tag_id=params.tag_id)

        # 只查询激活的策略
        search_q &= Q(is_active=True)

        # 排序
        order = []
        if params.sort_by:
            order_field = (
                f"-{params.sort_by}" if params.sort_order == "desc" else params.sort_by
            )
            order.append(order_field)
        else:
            order.append("-updated_at")  # 默认按更新时间倒序

        # 预加载关联数据
        prefetch = ["performance", "tag_relations__tag"]

        # 调用基类方法获取数据
        total, strategies = await self.get_list(
            page=params.page,
            page_size=params.page_size,
            search=search_q,
            order=order,
            prefetch=prefetch,
            distinct=True if params.tag_id else False,
        )

        # 转换为前端需要的格式
        result = []
        for strategy in strategies:
            # 获取绩效数据
            performance = getattr(strategy, "performance", None)
            returns = performance.latest_return if performance else 0
            win_rate = performance.latest_win_rate if performance else 0

            # 获取标签列表
            tags = []
            if hasattr(strategy, "tag_relations"):
                tags = [rel.tag.name for rel in strategy.tag_relations if rel.tag]

            item_dict = {
                "id": str(strategy.id),
                "name": strategy.name,
                "description": strategy.description,
                "status": strategy.status,
                "returns": float(returns),
                "win_rate": float(win_rate),
                "tags": tags,
                "updated_at": strategy.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            result.append(item_dict)

        return total, result

    async def create_with_tags(self, obj_in: StrategyCreateSchema) -> Strategy:
        """创建策略（包含标签关联）"""
        async with in_transaction():
            # 提取标签ID
            tag_ids = obj_in.tag_ids
            obj_dict = obj_in.model_dump(exclude={"tag_ids"})

            # 创建策略
            strategy = await self.create(obj_dict)

            # 创建绩效记录
            await StrategyPerformance.create(strategy=strategy)

            # 关联标签
            if tag_ids:
                await self._associate_tags(strategy, tag_ids)

            return strategy

    async def update_with_tags(self, id: str, obj_in: StrategyUpdateSchema) -> Strategy:
        """更新策略（包含标签关联）"""
        async with in_transaction():
            # 提取标签ID
            tag_ids = obj_in.tag_ids
            obj_dict = obj_in.model_dump(exclude={"tag_ids"}, exclude_unset=True)

            # 更新策略
            strategy = await self.update(id, obj_dict)

            # 更新标签关联
            if tag_ids is not None:
                # 删除现有关联
                await StrategyTagRelation.filter(strategy=strategy).delete()
                # 创建新关联
                if tag_ids:
                    await self._associate_tags(strategy, tag_ids)

            return strategy

    async def _associate_tags(self, strategy: Strategy, tag_ids: List[str]):
        """关联标签"""
        for tag_id in tag_ids:
            tag = await StrategyTag.get_or_none(id=tag_id)
            if tag:
                await StrategyTagRelation.create(strategy=strategy, tag=tag)

    async def get_with_details(self, id: str) -> Optional[Strategy]:
        """获取策略详情（包含所有关联数据）"""
        return (
            await Strategy.filter(id=id)
            .prefetch_related(
                "tag_relations__tag", "performance", "backtests", "executions"
            )
            .first()
        )


class StrategyTagService(BaseService[StrategyTag, StrategyTagCreateSchema, dict]):
    """策略标签服务"""

    def __init__(self):
        super().__init__(StrategyTag)

    async def get_all_tags(self) -> List[StrategyTag]:
        """获取所有标签"""
        return await StrategyTag.all().order_by("name")


# 创建服务实例
strategy_service = StrategyService()
strategy_tag_service = StrategyTagService()
