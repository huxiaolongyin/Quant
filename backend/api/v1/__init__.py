from fastapi import APIRouter

from .dashboard import router as dashboard_router
from .market import router as market_router
from .sync import router as sync_router

router = APIRouter()

router.include_router(dashboard_router, prefix="/overview", tags=["总览"])
router.include_router(market_router, prefix="/watchlist", tags=["自选股票"])
router.include_router(sync_router, prefix="/sync", tags=["数据同步"])
