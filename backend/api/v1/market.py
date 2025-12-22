"""自选行情，关注自选股票的实时/历史行情展示"""

from datetime import date
from typing import List, Literal

from aiocache import Cache, cached
from fastapi import APIRouter, HTTPException, Query, status

from backend.core.provider import get_price_quotes
from backend.models.stock import Stock
from backend.schemas.base import BaseResponse, OptionItem, PaginatedResponse
from backend.schemas.market import (
    DateBar,
    StockQuote,
    WatchlistStockCreate,
    WatchlistStockReorder,
    WatchlistStockResponse,
    WatchlistStockUpdate,
)
from backend.services.daily import daily_line_service
from backend.services.market import watchlist_stock_service

router = APIRouter()


@router.get(
    "/options",
    response_model=BaseResponse[List[OptionItem]],
    summary="获取可选股票列表",
)
@cached(ttl=300, cache=Cache.MEMORY)
async def get_stock_list():
    stocks = await Stock.all()
    data = [{"value": stock.id, "label": stock.full_stock_code} for stock in stocks]
    return BaseResponse[List[OptionItem]].success(data=data)


@router.get(
    "",
    response_model=PaginatedResponse[WatchlistStockResponse],
    summary="获取自选股票列表",
)
async def get_watchlist(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    # keyword: str | None = Query(None, description="搜索关键词"),
):
    total, items = await watchlist_stock_service.get_list(
        page=page, page_size=page_size
    )
    return PaginatedResponse.create(
        items=[WatchlistStockResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/realtime",
    response_model=BaseResponse[list[StockQuote]],
    summary="获取自选股票实时行情列表",
)
async def get_realtime_stock_data(
    force_refresh: bool = Query(False, description="是否强制刷新", alias="forceRefresh")
):
    """获取所有自选股票的实时行情数据"""
    # 1. 获取所有自选股票
    _, items = await watchlist_stock_service.get_list(page=1, page_size=100)

    if not items:
        return BaseResponse.success(data=[])

    # 2. 预加载关联的 stock 信息，收集股票代码
    holding_stocks = [(item.stock_code, item.holding_num) for item in items]

    stock_quotes = get_price_quotes(holding_stocks, force_refresh)

    return BaseResponse[list[StockQuote]].success(data=stock_quotes)


@router.get(
    "/{id}",
    response_model=BaseResponse[WatchlistStockResponse],
    summary="获取自选股票详情",
)
async def get_watchlist_stock(id: int):
    """根据ID获取自选股票详情"""
    item = await watchlist_stock_service.get(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="自选股票不存在",
        )
    return BaseResponse[WatchlistStockResponse].success(
        data=WatchlistStockResponse.model_validate(item)
    )


@router.post(
    "",
    response_model=BaseResponse[WatchlistStockResponse],
    status_code=status.HTTP_201_CREATED,
    summary="添加自选股票",
)
async def create_watchlist_stock(data: WatchlistStockCreate):
    """添加股票到自选"""
    # 检查是否已存在
    if await watchlist_stock_service.is_stock_in_watchlist(data.stock_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该股票已在自选列表中",
        )

    item = await watchlist_stock_service.create(data)
    # 重新查询以获取关联数据
    item = await watchlist_stock_service.get(item.id)
    return BaseResponse[WatchlistStockResponse].success(
        data=WatchlistStockResponse.model_validate(item)
    )


@router.put(
    "/{id}",
    response_model=BaseResponse[WatchlistStockResponse],
    summary="更新自选股票",
)
async def update_watchlist_stock(id: int, data: WatchlistStockUpdate):
    """更新自选股票信息"""
    item = await watchlist_stock_service.update(id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="自选股票不存在",
        )
    item = await watchlist_stock_service.get(id)
    return BaseResponse[WatchlistStockResponse].success(
        data=WatchlistStockResponse.model_validate(item)
    )


@router.delete(
    "/{id}",
    response_model=BaseResponse,
    summary="删除自选股票",
)
async def delete_watchlist_stock(id: int):
    """从自选中删除股票"""
    success = await watchlist_stock_service.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="自选股票不存在",
        )
    return BaseResponse.success(message="删除成功")


@router.post(
    "/reorder",
    response_model=BaseResponse[dict],
    summary="调整排序",
)
async def reorder_watchlist(data: WatchlistStockReorder):
    """调整自选股票排序"""
    updated = await watchlist_stock_service.reorder(data.items)
    return BaseResponse[dict].success(data={"updated": updated})


@router.get(
    "/{id}/history", response_model=BaseResponse, summary="获取单只股票历史行情"
)
async def get_history_quotes(
    id: int,
    period: Literal["daily", "weekly", "monthly"] = "daily",
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    limit: int = Query(250, ge=1, le=1000, description="返回数量"),
):
    """
    获取股票历史行情数据

    - **period**: daily(日线) / weekly(周线) / monthly(月线)
    - 周线/月线会从日线数据聚合计算
    """
    # 1. 获取自选股票信息，拿到 stock_code
    watchlist = await watchlist_stock_service.get(id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="自选股票不存在")

    # 需要预加载关联的 stock 获取 stock_code
    await watchlist.fetch_related("stock")
    stock_code = watchlist.stock.full_stock_code

    # 2. 获取日线数据（周/月线需要更多数据来聚合）
    fetch_limit = limit if period == "daily" else limit * 31
    daily_data = await daily_line_service.get_history(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        limit=fetch_limit,
    )

    if not daily_data:
        return BaseResponse.success(data=[])

    # 3. 根据 period 处理
    if period == "daily":
        # 将日线数据转换为 DateBar 对象
        date_bars = [
            DateBar(
                stock_code=d.stock_code,
                trade_date=d.trade_date,
                open=d.open,
                high=d.high,
                low=d.low,
                close=d.close,
                volume=d.volume,
                turnover=d.turnover,
            )
            for d in daily_data
        ]
        return BaseResponse[List[DateBar]].success(data=date_bars)

    return BaseResponse[List[DateBar]].success(
        data=_aggregate_kline(stock_code, daily_data, period, limit)
    )


def _aggregate_kline(
    stock_code: str,
    daily_data: list,
    period: Literal["weekly", "monthly"],
    limit: int,
) -> list[DateBar]:
    """将日线聚合为周线/月线"""
    from collections import defaultdict
    from decimal import Decimal

    groups = defaultdict(list)

    for item in daily_data:
        td = item.trade_date
        if period == "weekly":
            # 按周分组 (ISO 周)
            key = td.isocalendar()[:2]  # (year, week)
        else:
            # 按月分组
            key = (td.year, td.month)
        groups[key].append(item)

    result = []
    for key in sorted(groups.keys(), reverse=True)[:limit]:
        items = sorted(groups[key], key=lambda x: x.trade_date)
        result.append(
            DateBar(
                stock_code=stock_code,
                trade_date=items[-1].trade_date,
                open=items[0].open,
                close=items[-1].close,
                high=max(i.high for i in items),
                low=min(i.low for i in items),
                volume=sum(i.volume for i in items),
                turnover=sum(i.turnover or Decimal(0) for i in items),
            )
        )

    return result[::-1]
