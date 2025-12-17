"""策略工厂，内置 RSI、MACD、均线等策略，支持自定义"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/templates", summary="获取内置策略模板列表")
async def get_strategy_templates():
    """RSI、MACD、双均线、布林带、海龟等内置策略"""
    pass


@router.get("", summary="获取用户策略列表")
async def get_strategies():
    pass


@router.get("/{id}", summary="获取策略详情")
async def get_strategy_detail(id: int):
    pass


@router.post("", summary="添加策略")
async def create_strategy():
    pass


@router.put("/{id}", summary="更新策略")
async def update_strategy(id: int):
    pass


@router.delete("/{id}", summary="删除策略")
async def delete_strategy(id: int):
    pass
