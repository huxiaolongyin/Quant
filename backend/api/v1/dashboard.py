from fastapi import APIRouter
from backend.services.market import watchlist_stock_service
from backend.core.provider import get_price_quotes
from backend.schemas.base import BaseResponse

router = APIRouter()


@router.get("", summary="获取系统概览、持仓收益、策略运行状态")
async def get_overview():

    _, items = await watchlist_stock_service.get_list(page=1, page_size=100)
    holding_stocks = [(item.get("stockCode"), item.get("holdingNum")) for item in items]

    stock_quotes = get_price_quotes(holding_stocks)

    # 持仓市值
    total_market = sum([stock.get("price") for stock in stock_quotes])

    # 今日收益率
    yesterday_market = sum([stock.get("yesterdayPrice") for stock in stock_quotes])
    rate = round(total_market / yesterday_market - 1, 4)

    return BaseResponse.success(data={"totalMarket": total_market, "rate": rate})


@router.get("/charts", summary="获取图表数据")
async def get_charts():
    pass
