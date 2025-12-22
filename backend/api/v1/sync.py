from fastapi import APIRouter, BackgroundTasks, Query

from backend.schemas import (
    BaseResponse,
    PaginatedData,
    SyncLogItem,
    SyncSummaryResponse,
    TriggerRequest,
)
from backend.services.sync import sync_service

router = APIRouter()


@router.get(
    "/summary",
    response_model=BaseResponse[SyncSummaryResponse],
    summary="获取同步状态概览",
)
async def get_sync_summary():
    return BaseResponse[SyncSummaryResponse].success(
        data=await sync_service.get_summary()
    )


@router.get(
    "/logs",
    response_model=BaseResponse[PaginatedData[SyncLogItem]],
    summary="获取同步日志",
)
async def get_sync_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量", alias="pageSize"),
):

    return BaseResponse.success(
        data=await sync_service.get_logs(page=page, page_size=page_size)
    )


@router.post(
    "/trigger",
    response_model=BaseResponse,
    summary="触发同步任务",
)
async def trigger_sync_task(body: TriggerRequest, background_tasks: BackgroundTasks):

    try:
        background_tasks.add_task(
            sync_service.trigger_task,
            type=body.type,
            payload=body.payload,
        )

        return BaseResponse.success(message="任务已提交到后台队列")

    except Exception as e:
        return BaseResponse.error(message=str(e))
