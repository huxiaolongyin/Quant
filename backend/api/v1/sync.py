from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Query

from backend.schemas import (
    BaseResponse,
    PaginatedData,
    SyncLogItem,
    SyncSummaryResponse,
    TriggerRequest,
    SchedulerUpdateRequest,
)
from backend.services.sync import sync_service
from backend.utils import get_previous_trading_day

router = APIRouter()


@router.get("/summary", response_model=BaseResponse[SyncSummaryResponse], summary="获取同步状态概览")
async def get_sync_summary():
    return BaseResponse[SyncSummaryResponse].success(data=await sync_service.get_summary())


@router.get("/logs", response_model=BaseResponse[PaginatedData[SyncLogItem]], summary="获取同步日志")
async def get_sync_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量", alias="pageSize"),
):

    return BaseResponse.success(data=await sync_service.get_logs(page=page, page_size=page_size))


@router.post("/trigger", response_model=BaseResponse, summary="触发同步任务")
async def trigger_sync_task(body: TriggerRequest, background_tasks: BackgroundTasks):
    today = datetime.today()
    previous_trading_day = datetime.strptime(await get_previous_trading_day(), "%Y-%m-%d")

    if not body.data_range:
        start_date = previous_trading_day
        end_date = today if datetime.now().hour >= 16 else previous_trading_day
    elif len(body.data_range) == 1:
        start_date = datetime.strptime(body.data_range[0], "%Y-%m-%d")
        end_date = today if datetime.now().hour >= 16 else previous_trading_day
    else:
        start_date = datetime.strptime(body.data_range[0], "%Y-%m-%d")
        end_date = datetime.strptime(body.data_range[1], "%Y-%m-%d")

    try:
        background_tasks.add_task(sync_service.sync_stock_daily_line, start_date=start_date, end_date=end_date)

        return BaseResponse.success(message="任务已提交到后台队列")

    except Exception as e:
        return BaseResponse.error(message=str(e))


@router.put("/scheduler", response_model=BaseResponse, summary="更新调度配置")
async def update_scheduler_config(body: SchedulerUpdateRequest):
    try:
        await sync_service.update_scheduler_config(enabled=body.enabled, time=body.time)
        return BaseResponse.success(message="调度配置已更新")
    except Exception as e:
        return BaseResponse.error(message=str(e))
