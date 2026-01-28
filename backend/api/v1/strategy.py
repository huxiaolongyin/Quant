"""策略工厂，内置 RSI、MACD、均线等策略，支持自定义"""

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.strategy import (
    StrategyBacktestCreateSchema,
    StrategyBacktestSchema,
    StrategyCreateSchema,
    StrategyListItemSchema,
    StrategyListParams,
    StrategySchema,
    StrategyTagCreateSchema,
    StrategyTagSchema,
    StrategyUpdateSchema,
)
from backend.services.strategy import strategy_service, strategy_tag_service

router = APIRouter()


@router.get("/templates", summary="获取内置策略模板列表")
async def get_strategy_templates():
    """RSI、MACD、双均线、布林带、海龟等内置策略"""
    pass


@router.get(
    "",
    response_model=PaginatedResponse[StrategyListItemSchema],
    summary="获取策略列表",
    description="支持搜索、筛选、分页的策略列表接口",
)
async def get_strategy_list(params: StrategyListParams = Depends()):
    """获取策略列表"""
    try:
        total, strategies = await strategy_service.get_list_with_performance(params)

        return PaginatedResponse.create(
            items=strategies, total=total, page=params.page, page_size=params.page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/{strategy_id}", summary="获取策略详情")
async def get_strategy_detail(strategy_id: int):
    """获取策略详情"""
    strategy = await strategy_service.get_with_details(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    # 转换为响应格式
    strategy_dict = await strategy.to_dict(m2m=True)

    return BaseResponse.success(data=strategy_dict)


@router.post("", response_model=BaseResponse[StrategySchema], summary="创建策略")
async def create_strategy(strategy_in: StrategyCreateSchema):
    """创建新策略"""
    try:
        strategy = await strategy_service.create_with_tags(strategy_in)
        strategy_dict = await strategy.to_dict()

        return BaseResponse.success(data=strategy_dict, message="策略创建成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建策略失败: {str(e)}")


@router.put(
    "/{strategy_id}", response_model=BaseResponse[StrategySchema], summary="更新策略"
)
async def update_strategy(strategy_id: str, strategy_in: StrategyUpdateSchema):
    """更新策略"""
    try:
        strategy = await strategy_service.update_with_tags(strategy_id, strategy_in)
        strategy_dict = await strategy.to_dict()

        return BaseResponse.success(data=strategy_dict, message="策略更新成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新策略失败: {str(e)}")


@router.delete("/{strategy_id}", response_model=BaseResponse, summary="删除策略")
async def delete_strategy(strategy_id: str):
    """删除策略（软删除）"""
    try:
        strategy = await strategy_service.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        # 软删除：设置为非激活状态
        await strategy_service.update(strategy_id, {"is_active": False})

        return BaseResponse.success(message="策略删除成功")
    except Exception as e:
        return BaseResponse.error(message=f"删除策略失败: {str(e)}")


@router.post(
    "/{strategy_id}/backtest", response_model=BaseResponse[str], summary="启动策略回测"
)
async def start_backtest(strategy_id: str, backtest_in: StrategyBacktestCreateSchema):
    """启动策略回测"""
    try:
        # 验证策略是否存在
        strategy = await strategy_service.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        # TODO: 这里应该启动异步回测任务
        # 现在只是返回成功消息
        return BaseResponse.success(
            data=f"策略 {strategy.name} 回测已启动", message="回测启动成功"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"启动回测失败: {str(e)}")


# =====================================================================
#                           标签相关接口
# =====================================================================


@router.get(
    "/tags",
    response_model=BaseResponse[list[StrategyTagSchema]],
    summary="获取所有策略标签",
)
async def get_all_tags():
    """获取所有策略标签"""
    try:
        tags = await strategy_tag_service.get_all_tags()
        tags_dict = [await tag.to_dict() for tag in tags]

        return BaseResponse.success(data=tags_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")


@router.post("/tags", summary="创建策略标签")
async def create_tags(tag_in: StrategyTagCreateSchema):
    tag = await strategy_tag_service.create(tag_in)
    return BaseResponse.success(message="标签创建成功", data=tags_dict)
