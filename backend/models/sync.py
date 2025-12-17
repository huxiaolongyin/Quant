from tortoise import fields, models

from backend.enums.sync import SyncStatus, SyncType


class SyncLog(models.Model):
    """记录同步任务的执行历史"""

    id = fields.IntField(pk=True)
    type = fields.CharEnumField(SyncType, max_length=20, default=SyncType.MANUAL)
    range_desc = fields.CharField(
        max_length=100, description="Description of the date range synced"
    )
    start_time = fields.DatetimeField(auto_now_add=True)
    end_time = fields.DatetimeField(null=True)
    status = fields.CharEnumField(SyncStatus, max_length=20, default=SyncStatus.RUNNING)
    error_msg = fields.TextField(null=True)

    class Meta:
        table = "sync_logs"
        ordering = ["-start_time"]

    def duration(self) -> str:
        """计算持续时间字符串"""
        if self.end_time and self.start_time:
            delta = (self.end_time - self.start_time).total_seconds()
            return f"{int(delta)}s"
        return "-"


class SyncConfig(models.Model):
    """用于存储调度程序配置的单例表"""

    id = fields.IntField(pk=True)
    scheduler_enabled = fields.BooleanField(default=True)
    scheduler_time = fields.CharField(max_length=10, default="17:30")

    # We might store the global 'running' state here or derive it from active logs
    current_status = fields.CharEnumField(
        SyncStatus, max_length=20, default=SyncStatus.IDLE
    )

    class Meta:
        table = "sync_config"
