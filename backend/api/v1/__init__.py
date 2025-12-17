from fastapi import APIRouter

from .market import router as market_router
from .sync import router as sync_router

router = APIRouter()


router.include_router(sync_router, prefix="/sync", tags=["数据同步"])
router.include_router(market_router, prefix="/watchlist", tags=["自选股票"])
