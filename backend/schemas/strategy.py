from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from backend.models.strategy import ExecutionStatus, StrategyStatus
from backend.schemas.base import (
    BaseSchema,
    PaginationParams,
    SortParams,
    TimestampMixin,
    UUIDMixin,
)

# =====================================================================
#                           策略标签Schema
# =====================================================================


class StrategyTagSchema(BaseSchema, UUIDMixin, TimestampMixin):
    """策略标签响应模型"""

    name: str = Field(..., description="标签名称")
    color: str = Field(..., description="标签颜色")
    description: Optional[str] = Field(None, description="标签描述")


class StrategyTagCreateSchema(BaseSchema):
    """创建策略标签请求模型"""

    name: str = Field(..., description="标签名称", max_length=50)
    color: str = Field(default="#1890ff", description="标签颜色", max_length=20)
    description: Optional[str] = Field(None, description="标签描述", max_length=200)


# =====================================================================
#                           策略Schema
# =====================================================================


class StrategyListItemSchema(BaseSchema, UUIDMixin):
    """策略列表项模型（用于列表页面）"""

    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    status: StrategyStatus = Field(..., description="策略状态")

    # 绩效数据（来自StrategyPerformance）
    returns: Decimal = Field(default=Decimal("0"), description="累计收益率(%)")
    win_rate: Decimal = Field(default=Decimal("0"), description="胜率(%)")

    # 标签列表
    tags: List[str] = Field(default_factory=list, description="策略标签")

    # 时间字段
    updated_at: str = Field(..., description="更新时间")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class StrategySchema(BaseSchema, UUIDMixin, TimestampMixin):
    """策略详情响应模型"""

    name: str = Field(..., description="策略名称", examples=["RSI策略"])
    description: Optional[str] = Field(
        None, description="策略描述", examples=["RSI策略"]
    )
    code: str = Field(..., description="策略代码")
    status: StrategyStatus = Field(..., description="策略状态")
    is_active: bool = Field(..., description="是否激活")

    # 策略参数
    parameters: dict = Field(default_factory=dict, description="策略参数配置")

    # 风控配置
    max_position_size: Optional[Decimal] = Field(None, description="最大仓位")
    stop_loss_ratio: Optional[Decimal] = Field(None, description="止损比例")
    take_profit_ratio: Optional[Decimal] = Field(None, description="止盈比例")

    # 创建者
    created_by: Optional[str] = Field(None, description="创建者")

    # 关联数据
    tags: List[StrategyTagSchema] = Field(default_factory=list, description="策略标签")

    class Config:
        json_encoders = {Decimal: lambda v: float(v) if v else None}


class StrategyCreateSchema(BaseSchema):
    """创建策略请求模型"""

    name: str = Field(..., description="策略名称", max_length=200, examples=["RSI策略"])
    description: Optional[str] = Field(
        None, description="策略描述", examples=["RSI策略"]
    )
    code: str = Field(..., description="策略代码")

    # 策略参数
    parameters: dict = Field(default_factory=dict, description="策略参数配置")

    # 风控配置
    max_position_size: Optional[Decimal] = Field(
        None, description="最大仓位", ge=0, le=1
    )
    stop_loss_ratio: Optional[Decimal] = Field(None, description="止损比例", ge=0, le=1)
    take_profit_ratio: Optional[Decimal] = Field(None, description="止盈比例", ge=0)

    # 标签ID列表
    tag_ids: List[str] = Field(default_factory=list, description="标签ID列表")


class StrategyUpdateSchema(BaseSchema):
    """更新策略请求模型"""

    name: Optional[str] = Field(None, description="策略名称", max_length=200)
    description: Optional[str] = Field(None, description="策略描述")
    code: Optional[str] = Field(None, description="策略代码")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")

    # 策略参数
    parameters: Optional[dict] = Field(None, description="策略参数配置")

    # 风控配置
    max_position_size: Optional[Decimal] = Field(
        None, description="最大仓位", ge=0, le=1
    )
    stop_loss_ratio: Optional[Decimal] = Field(None, description="止损比例", ge=0, le=1)
    take_profit_ratio: Optional[Decimal] = Field(None, description="止盈比例", ge=0)

    # 标签ID列表
    tag_ids: Optional[List[str]] = Field(None, description="标签ID列表")


# =====================================================================
#                           回测相关Schema
# =====================================================================


class StrategyBacktestSchema(BaseSchema, UUIDMixin, TimestampMixin):
    """策略回测结果模型"""

    strategy_id: str = Field(..., description="策略ID")
    name: str = Field(..., description="回测名称")

    # 回测基本信息
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")

    # 资金信息
    initial_capital: Decimal = Field(..., description="初始资金")
    final_capital: Optional[Decimal] = Field(None, description="最终资金")

    # 绩效指标
    total_return: Optional[Decimal] = Field(None, description="总收益率(%)")
    annual_return: Optional[Decimal] = Field(None, description="年化收益率(%)")
    max_drawdown: Optional[Decimal] = Field(None, description="最大���撤(%)")
    sharpe_ratio: Optional[Decimal] = Field(None, description="夏普比率")
    win_rate: Optional[Decimal] = Field(None, description="胜率(%)")

    # 交易统计
    trade_count: int = Field(default=0, description="总交易次数")
    win_count: int = Field(default=0, description="盈利交易次数")
    loss_count: int = Field(default=0, description="亏损交易次数")

    # 状态
    status: ExecutionStatus = Field(..., description="回测状态")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_encoders = {Decimal: lambda v: float(v) if v else None}


class StrategyBacktestCreateSchema(BaseSchema):
    """创建回测请求模型"""

    strategy_id: str = Field(..., description="策略ID")
    name: str = Field(..., description="回测名称", max_length=200)
    start_date: str = Field(
        ..., description="回测开始日期", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ..., description="回测结束日期", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    initial_capital: Decimal = Field(..., description="初始资金", gt=0)


# =====================================================================
#                           查询参数Schema
# =====================================================================


class StrategyListParams(PaginationParams, SortParams):
    """策略列表查询参数"""

    search: Optional[str] = Field(None, description="搜索关键词（策略名称）")
    status: Optional[StrategyStatus] = Field(None, description="策略状态筛选")
    tag_id: Optional[str] = Field(None, description="标签ID筛选")
    created_by: Optional[str] = Field(None, description="创建者筛选")
