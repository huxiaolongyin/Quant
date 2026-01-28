from enum import Enum


class StrategyStatus(str, Enum):
    """策略状态枚举"""

    DRAFT = "draft"  # 草稿
    RUNNING = "running"  # 运行中
    STOPPED = "stopped"  # 已停止
    BACKTEST = "backtest"  # 回测中
    ERROR = "error"  # 错误状态


class ExecutionStatus(str, Enum):
    """执行状态枚举"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class VersionStatus(str, Enum):
    """版本状态枚举"""

    DRAFT = "draft"  # 草稿
    TESTING = "testing"  # 测试中
    ACTIVE = "active"  # 活跃版本
    ARCHIVED = "archived"  # 已归档


class TradeType(str, Enum):
    """交易类型枚举"""

    BUY = "BUY"  # 买入
    SELL = "SELL"  # 卖出
