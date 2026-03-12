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
from backend.strategy_templates import (
    CodeValidateRequest,
    CodeValidateResponse,
    StrategyFromTemplateRequest,
    StrategyTemplateListItem,
    registry,
    validate_code,
)

router = APIRouter()


@router.get(
    "/templates",
    response_model=BaseResponse[list[StrategyTemplateListItem]],
    summary="获取内置策略模板列表",
)
async def get_strategy_templates(category: str = None):
    """获取所有内置策略模板列表（RSI、MACD、双均线、布林带、量价等）"""
    templates = registry.list_all(category=category)
    return BaseResponse.success(data=templates)


@router.get(
    "/templates/{template_id}",
    response_model=BaseResponse,
    summary="获取策略模板详情",
)
async def get_strategy_template(template_id: str):
    """获取单个策略模板的完整信息（包含代码）"""
    template = registry.get_full(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return BaseResponse.success(data=template.model_dump())


@router.post(
    "/validate-code",
    response_model=CodeValidateResponse,
    summary="验证策略代码安全性",
)
async def validate_strategy_code(request: CodeValidateRequest):
    """实时验证策略代码的安全性，检查是否包含危险模块和函数"""
    result = validate_code(request.code)
    return CodeValidateResponse(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings,
    )


@router.post(
    "/from-template",
    response_model=BaseResponse[StrategySchema],
    summary="从模板创建策略",
)
async def create_strategy_from_template(request: StrategyFromTemplateRequest):
    """基于模板创建新策略，可自定义参数"""
    template = registry.get_full(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    strategy_in = StrategyCreateSchema(
        name=request.name,
        description=request.description or template.description,
        code=template.code,
        parameters=request.params,
        tag_ids=request.tag_ids,
    )

    try:
        strategy = await strategy_service.create_with_tags(strategy_in)
        strategy_dict = await strategy.to_dict()
        return BaseResponse.success(data=StrategySchema.model_validate(strategy_dict), message="策略创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建策略失败: {str(e)}")


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

        return PaginatedResponse.create(items=strategies, total=total, page=params.page, page_size=params.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/{strategy_id}", summary="获取策略详情")
async def get_strategy_detail(strategy_id: str):
    """获取策略详情"""
    strategy = await strategy_service.get_with_details(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    strategy_dict = await strategy.to_dict(m2m=True)

    # 获取当前版本代码
    current_version = await strategy.get_current_version()
    if current_version:
        strategy_dict["code"] = current_version.code
        strategy_dict["versionNumber"] = current_version.version_number
    else:
        strategy_dict["code"] = ""
        strategy_dict["versionNumber"] = None

    return BaseResponse.success(data=strategy_dict)


@router.post("", response_model=BaseResponse[StrategySchema], summary="创建策略")
async def create_strategy(strategy_in: StrategyCreateSchema):
    """创建新策略（自定义代码）"""
    try:
        strategy = await strategy_service.create_with_tags(strategy_in)
        strategy_dict = await strategy.to_dict()

        return BaseResponse.success(data=strategy_dict, message="策略创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建策略失败: {str(e)}")


@router.put("/{strategy_id}", response_model=BaseResponse[StrategySchema], summary="更新策略")
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

        await strategy_service.update(strategy_id, {"is_active": False})

        return BaseResponse.success(message="策略删除成功")
    except Exception as e:
        return BaseResponse.error(message=f"删除策略失败: {str(e)}")


@router.post("/{strategy_id}/backtest", response_model=BaseResponse[str], summary="启动策略回测")
async def start_backtest(strategy_id: str, backtest_in: StrategyBacktestCreateSchema):
    """启动策略回测"""
    try:
        strategy = await strategy_service.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        return BaseResponse.success(data=f"策略 {strategy.name} 回测已启动", message="回测启动成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"启动回测失败: {str(e)}")


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
    """创建策略标签"""
    try:
        tag = await strategy_tag_service.create(tag_in)
        tag_dict = await tag.to_dict()
        return BaseResponse.success(message="标签创建成功", data=tag_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建标签失败: {str(e)}")
