from __future__ import annotations

from tortoise import fields

from backend.enums.notification import ChannelType

from .base import BaseModel, TimestampMixin


class NotificationChannel(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, description="channel name")
    channel_type = fields.CharEnumField(ChannelType, description="channel type")
    webhook_url = fields.CharField(max_length=500, description="webhook url")
    secret = fields.CharField(max_length=200, null=True, description="sign secret")
    is_enabled = fields.BooleanField(default=True, description="enabled")

    class Meta:
        table = "notification_channels"
        table_description = "notification channels"
