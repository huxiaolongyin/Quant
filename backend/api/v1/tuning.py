"""参数调优，基于 Optuna 的策略参数自动优化"""

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="获取调优记录")
async def get_tuning_record():
    pass


@router.post("", summary="添加调优训练")
async def add_tuning_training():
    pass
