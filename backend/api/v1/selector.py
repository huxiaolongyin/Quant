"""选股器 API 路由"""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.models.selector import Selector, SelectorResult
from backend.models.stock import Stock
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.selector import (
    SelectorCreateSchema,
    SelectorFieldSchema,
    SelectorListItemSchema,
    SelectorListParams,
    SelectorResultSchema,
    SelectorSchema,
    SelectorUpdateSchema,
)
from backend.services.selector_engine import selector_engine
from backend.services.selector_service import SelectorService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SelectorListItemSchema],
    summary="获取选股器列表",
)
async def get_selector_list(params: SelectorListParams = Depends()):
    try:
        query = Selector.all()
        if params.name:
            query = query.filter(name__icontains=params.name)
        if params.is_active is not None:
            query = query.filter(is_active=params.is_active)

        total = await query.count()
        selectors = await query.offset(params.offset).limit(params.limit).order_by("-created_at")

        items = []
        for s in selectors:
            latest_result = await SelectorResult.filter(selector_id=s.id).order_by("-trade_date").first()
            result_count = await SelectorResult.filter(selector_id=s.id).count()

            items.append(
                SelectorListItemSchema(
                    id=s.id,
                    name=s.name,
                    description=s.description,
                    is_active=s.is_active,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    result_count=result_count,
                    last_result_date=latest_result.trade_date if latest_result else None,
                    last_result_count=latest_result.count if latest_result else None,
                )
            )

        return PaginatedResponse.create(items=items, total=total, page=params.page, page_size=params.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股器列表失败: {str(e)}")


@router.get("/fields", response_model=BaseResponse[List[SelectorFieldSchema]], summary="获取可筛选字段")
async def get_selector_fields():
    try:
        fields = await selector_engine.get_field_definitions()
        return BaseResponse.success(data=[SelectorFieldSchema.model_validate(field) for field in fields])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字段定义失败: {str(e)}")


@router.get("/options", response_model=BaseResponse[List[dict]], summary="获取字段选项")
async def get_selector_options(
    field: str = Query(..., description="字段名: industry, province, city"),
    province: str | None = Query(None, description="省份(用于城市联动)"),
):
    try:
        if field not in ("industry", "province", "city"):
            raise HTTPException(status_code=400, detail="field 必须是 industry, province 或 city")

        if field == "industry":
            values = (
                await Stock.filter(industry__isnull=False)
                .distinct()
                .order_by("industry")
                .values_list("industry", flat=True)
            )
            options = [{"label": v, "value": v} for v in values if v]
        elif field == "province":
            values = (
                await Stock.filter(province__isnull=False)
                .distinct()
                .order_by("province")
                .values_list("province", flat=True)
            )
            options = [{"label": v, "value": v} for v in values if v]
        else:
            query = Stock.filter(city__isnull=False)
            if province:
                query = query.filter(province=province)
            values = await query.distinct().order_by("city").values_list("city", flat=True)
            options = [{"label": v, "value": v} for v in values if v]

        return BaseResponse.success(data=options)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选项失败: {str(e)}")


@router.get("/{selector_id}", response_model=BaseResponse[SelectorSchema], summary="获取选股器详情")
async def get_selector_detail(selector_id: int):
    try:
        selector = await Selector.get_or_none(id=selector_id)
        if not selector:
            raise HTTPException(status_code=404, detail="选股器不存在")

        data = await SelectorService.to_json(selector)
        return BaseResponse.success(data=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股器详情失败: {str(e)}")


@router.post("", response_model=BaseResponse[SelectorSchema], summary="创建选股器")
async def create_selector(selector_in: SelectorCreateSchema):
    try:
        rule_dict = selector_in.rule.model_dump()
        selector = await SelectorService.create_from_json(
            name=selector_in.name,
            rule=rule_dict,
            description=selector_in.description or "",
        )
        data = await SelectorService.to_json(selector)
        return BaseResponse.success(data=data, message="选股器创建成功")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建选股器失败: {str(e)}")


@router.put("/{selector_id}", response_model=BaseResponse[SelectorSchema], summary="更新选股器")
async def update_selector(selector_id: int, selector_in: SelectorUpdateSchema):
    try:
        selector = await Selector.get_or_none(id=selector_id)
        if not selector:
            raise HTTPException(status_code=404, detail="选股器不存在")

        if selector_in.name is not None:
            selector.name = selector_in.name
        if selector_in.description is not None:
            selector.description = selector_in.description
        if selector_in.is_active is not None:
            selector.is_active = selector_in.is_active
        if selector_in.rule is not None:
            await SelectorService.update_rule(selector, selector_in.rule.model_dump())

        await selector.save()
        data = await SelectorService.to_json(selector)
        return BaseResponse.success(data=data, message="选股器更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新选股器失败: {str(e)}")


@router.delete("/{selector_id}", response_model=BaseResponse, summary="删除选股器")
async def delete_selector(selector_id: int):
    try:
        selector = await Selector.get_or_none(id=selector_id)
        if not selector:
            raise HTTPException(status_code=404, detail="选股器不存在")

        await selector.delete()
        return BaseResponse.success(message="选股器删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除选股器失败: {str(e)}")


@router.post("/{selector_id}/execute", response_model=BaseResponse[dict], summary="执行选股")
async def execute_selector(selector_id: int, trade_date: date | None = None):
    try:
        selector = await Selector.get_or_none(id=selector_id)
        if not selector:
            raise HTTPException(status_code=404, detail="选股器不存在")

        result = await selector_engine.execute(selector, trade_date)
        return BaseResponse.success(data=result, message="选股执行成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行选股失败: {str(e)}")


@router.get(
    "/{selector_id}/results",
    response_model=PaginatedResponse[SelectorResultSchema],
    summary="获取选股历史结果",
)
async def get_selector_results(
    selector_id: int,
    page: int = 1,
    page_size: int = 20,
):
    try:
        selector = await Selector.get_or_none(id=selector_id)
        if not selector:
            raise HTTPException(status_code=404, detail="选股器不存在")

        query = SelectorResult.filter(selector_id=selector_id)
        total = await query.count()
        results = await query.order_by("-trade_date", "-id").offset((page - 1) * page_size).limit(page_size)

        items = [
            SelectorResultSchema(
                id=r.id,
                selector_id=r.selector_id,
                trade_date=r.trade_date,
                stock_codes=r.stock_codes,
                count=r.count,
                execution_time=r.execution_time,
                created_at=r.created_at.isoformat(),
            )
            for r in results
        ]

        return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股结果失败: {str(e)}")


@router.get(
    "/{selector_id}/results/{result_id}",
    response_model=BaseResponse[SelectorResultSchema],
    summary="获取单次选股结果详情",
)
async def get_selector_result_detail(selector_id: int, result_id: int):
    try:
        result = await SelectorResult.get_or_none(id=result_id, selector_id=selector_id)
        if not result:
            raise HTTPException(status_code=404, detail="选股结果不存在")

        stocks = await selector_engine._get_stock_details(result.stock_codes)

        return BaseResponse.success(
            data=SelectorResultSchema(
                id=result.id,
                selector_id=result.selector_id,
                trade_date=result.trade_date,
                stock_codes=result.stock_codes,
                count=result.count,
                execution_time=result.execution_time,
                created_at=result.created_at.isoformat(),
                stocks=stocks,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股结果详情失败: {str(e)}")
