from enum import Enum


class SyncType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    BACKFILL = "backfill"


class SyncStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAIL = "fail"
