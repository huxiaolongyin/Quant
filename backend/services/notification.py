from typing import List, Optional

from backend.models.notification import NotificationChannel
from backend.notifiers import get_notifier
from backend.schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelOut,
    NotificationChannelUpdate,
    NotificationSend,
    NotificationTestResult,
)
from backend.services.base import BaseService


class NotificationChannelService(
    BaseService[NotificationChannel, NotificationChannelCreate, NotificationChannelUpdate]
):
    def __init__(self):
        super().__init__(NotificationChannel)

    async def get_all_enabled(self) -> List[NotificationChannel]:
        return await NotificationChannel.filter(is_enabled=True).all()

    async def send_notification(self, data: NotificationSend) -> dict:
        if data.channels:
            channels = await NotificationChannel.filter(
                notification_channel_id__in=data.channels, is_enabled=True
            ).all()
        else:
            channels = await self.get_all_enabled()

        if not channels:
            return {"total": 0, "success": 0, "failed": 0, "errors": ["No enabled channels"]}

        results = {"total": len(channels), "success": 0, "failed": 0, "errors": []}

        for channel in channels:
            try:
                notifier = get_notifier(
                    channel_type=channel.channel_type.value,
                    webhook_url=channel.webhook_url,
                    secret=channel.secret,
                )
                if data.is_markdown:
                    result = await notifier.send_markdown(data.title, data.content)

                else:
                    result = await notifier.send_text(data.content)

                if result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{channel.name}: send failed")

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{channel.name}: {str(e)}")

        return results

    async def test_channel(self, channel_id: int) -> NotificationTestResult:
        channel = await self.get(id=channel_id)
        if not channel:
            return NotificationTestResult(success=False, message="Channel not found")

        try:
            notifier = get_notifier(
                channel_type=channel.channel_type.value,
                webhook_url=channel.webhook_url,
                secret=channel.secret,
            )
            success, message = await notifier.test_connection()
            return NotificationTestResult(success=success, message=message)
        except Exception as e:
            return NotificationTestResult(success=False, message=str(e))

    async def toggle_enabled(self, channel_id: int, is_enabled: bool) -> Optional[NotificationChannel]:
        channel = await self.get(id=channel_id)
        if not channel:
            return None
        channel.is_enabled = is_enabled
        await channel.save()
        return channel


notification_channel_service = NotificationChannelService()
