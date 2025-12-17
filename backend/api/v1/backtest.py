from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="获取回测列表")
async def get_backtests():
    pass


@router.get("/run", summary="回测执行")
def run_backtest():
    pass
