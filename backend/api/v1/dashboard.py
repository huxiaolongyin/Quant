from fastapi import APIRouter

from backend.core.provider import get_price_quotes
from backend.schemas.base import BaseResponse
from backend.schemas.dashboard import OverView
from backend.services.market import watchlist_stock_service

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[OverView],
    summary="获取系统概览、持仓收益、策略运行状态",
)
async def get_overview():

    _, watchlist_items = await watchlist_stock_service.get_list(page=1, page_size=100)
    holdings = [(item.stock_code, item.holding_num) for item in watchlist_items]

    quotes = get_price_quotes(holdings)

    # 计算最新总持仓市值
    total_market_value = sum(q.market_value for q in quotes)

    # 计算上个工作日总市值
    yesterday_market_value = sum(q.pre_market_value for q in quotes)

    # 今日收益
    daily_return = total_market_value - yesterday_market_value
    # 今日收益率 (避免除零)
    daily_return_rate = (
        round(total_market_value / yesterday_market_value - 1, 4)
        if yesterday_market_value > 0
        else 0.0
    )

    data = OverView(
        total_market_value=total_market_value,
        daily_return=daily_return,
        daily_return_rate=daily_return_rate,
    )

    return BaseResponse[OverView].success(data=data)


@router.get("/charts", summary="获取图表数据")
async def get_charts():
    pass
