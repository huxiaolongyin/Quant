from typing import List

from fastapi import APIRouter

from backend.schemas.base import BaseResponse, PaginatedData
from backend.schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelOut,
    NotificationChannelUpdate,
    NotificationSend,
    NotificationTestResult,
)
from backend.services.notification import notification_channel_service

router = APIRouter()


@router.get("/channels", response_model=BaseResponse[List[NotificationChannelOut]])
async def get_channels():
    channels = await notification_channel_service.model.all().order_by("-created_at")
    return BaseResponse(
        data=[
            NotificationChannelOut(
                id=ch.id,
                name=ch.name,
                channel_type=ch.channel_type,
                webhook_url=ch.webhook_url,
                secret=ch.secret,
                is_enabled=ch.is_enabled,
                created_at=ch.created_at,
                updated_at=ch.updated_at,
            )
            for ch in channels
        ]
    )


@router.post("/channels", response_model=BaseResponse[NotificationChannelOut])
async def create_channel(data: NotificationChannelCreate):
    channel = await notification_channel_service.create(data)
    return BaseResponse(
        data=NotificationChannelOut(
            id=channel.id,
            name=channel.name,
            channel_type=channel.channel_type,
            webhook_url=channel.webhook_url,
            secret=channel.secret,
            is_enabled=channel.is_enabled,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
    )


@router.put("/channels/{channel_id}", response_model=BaseResponse[NotificationChannelOut])
async def update_channel(channel_id: int, data: NotificationChannelUpdate):
    channel = await notification_channel_service.update(channel_id, data)
    if not channel:
        return BaseResponse.error(message="Channel not found", code=404)
    return BaseResponse(
        data=NotificationChannelOut(
            id=channel.id,
            name=channel.name,
            channel_type=channel.channel_type,
            webhook_url=channel.webhook_url,
            secret=channel.secret,
            is_enabled=channel.is_enabled,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
    )


@router.delete("/channels/{channel_id}", response_model=BaseResponse)
async def delete_channel(channel_id: int):
    channel = await notification_channel_service.get(id=channel_id)
    if not channel:
        return BaseResponse.error(message="Channel not found", code=404)
    await channel.delete()
    return BaseResponse(message="Deleted successfully")


@router.post("/channels/{channel_id}/toggle", response_model=BaseResponse[NotificationChannelOut])
async def toggle_channel(channel_id: int, is_enabled: bool = True):
    channel = await notification_channel_service.toggle_enabled(channel_id, is_enabled)
    if not channel:
        return BaseResponse.error(message="Channel not found", code=404)
    return BaseResponse(
        data=NotificationChannelOut(
            id=channel.id,
            name=channel.name,
            channel_type=channel.channel_type,
            webhook_url=channel.webhook_url,
            secret=channel.secret,
            is_enabled=channel.is_enabled,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
    )


@router.post("/channels/{channel_id}/test", response_model=BaseResponse[NotificationTestResult])
async def test_channel(channel_id: int):
    result = await notification_channel_service.test_channel(channel_id)
    return BaseResponse(data=result)


@router.post("/send", response_model=BaseResponse[dict])
async def send_notification(data: NotificationSend):
    result = await notification_channel_service.send_notification(data)
    return BaseResponse(data=result)
