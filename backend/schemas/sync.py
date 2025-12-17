from typing import List, Literal, Optional

from pydantic import Field

from backend.enums.sync import SyncStatus, SyncType

from .base import BaseSchema


# --- 1. 同步概览 (Summary) 相关 ---
class SchedulerInfo(BaseSchema):
    enabled: bool
    time: str  # 格式如 "17:30"


class SyncSummaryResponse(BaseSchema):
    last_sync_time: int = Field(..., description="上次同步完成的时间戳")
    data_range: str = Field(..., description="当前数据覆盖的时间范围")
    stat_days: int = Field(..., description="统计天数")
    stock_count: int = Field(..., description="股票数量")
    scheduler: SchedulerInfo
    status: SyncStatus


# --- 2. 日志 (Logs) 相关 ---
class SyncLogItem(BaseSchema):
    id: str
    type: SyncType
    range: str
    start_time: str
    duration: str
    status: SyncStatus


# class SyncLogPageResponse(BaseSchema):
#     list: List[SyncLogItem]
#     total: int
#     page: int
#     page_size: int


# --- 3. 触发任务 (Trigger) 相关 ---
class TriggerRequest(BaseSchema):
    type: SyncType
    data_range: list
    payload: dict | None = None


class TriggerResponse(BaseSchema):
    success: bool
    msg: str
