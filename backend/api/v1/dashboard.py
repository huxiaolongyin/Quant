from fastapi import APIRouter

router = APIRouter()


@router.get("/overview", summary="获取系统概览、持仓收益、策略运行状态")
async def get_overview():
    pass


@router.get("/charts", summary="获取图表数据")
async def get_charts():
    pass
