from typing import List, Optional

from pydantic import Field

from backend.enums.notification import ChannelType
from backend.schemas.base import BaseSchema, IDMixin, TimestampMixin


class NotificationChannelCreate(BaseSchema):
    name: str = Field(..., description="channel name", max_length=50)
    channel_type: ChannelType = Field(..., description="channel type")
    webhook_url: str = Field(..., description="webhook url", max_length=500)
    secret: Optional[str] = Field(None, description="sign secret", max_length=200)
    is_enabled: bool = Field(default=True, description="enabled")


class NotificationChannelUpdate(BaseSchema):
    name: Optional[str] = Field(None, description="channel name", max_length=50)
    webhook_url: Optional[str] = Field(None, description="webhook url", max_length=500)
    secret: Optional[str] = Field(None, description="sign secret", max_length=200)
    is_enabled: Optional[bool] = Field(None, description="enabled")


class NotificationChannelOut(BaseSchema, IDMixin, TimestampMixin):
    name: str = Field(..., description="channel name")
    channel_type: ChannelType = Field(..., description="channel type")
    webhook_url: str = Field(..., description="webhook url")
    secret: Optional[str] = Field(None, description="sign secret")
    is_enabled: bool = Field(..., description="enabled")


class NotificationSend(BaseSchema):
    channels: Optional[List[int]] = Field(None, description="channel ids, empty means all enabled")
    title: str = Field(..., description="notification title")
    content: str = Field(..., description="notification content")
    is_markdown: bool = Field(default=False, description="use markdown format")


class NotificationTestResult(BaseSchema):
    success: bool = Field(..., description="test result")
    message: str = Field(..., description="result message")
