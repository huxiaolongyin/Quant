"""选股器 Schema 定义"""

from datetime import date
from typing import Any

from backend.schemas.base import BaseSchema, IDMixin, PaginationParams, TimestampMixin


class ConditionNodeSchema(BaseSchema):
    """条件节点"""

    id: int | None = None
    node_type: str
    logic: str | None = None
    field: str | None = None
    operator: str | None = None
    value: Any | None = None
    children: list["ConditionNodeSchema"] | None = None


ConditionNodeSchema.model_rebuild()


class SelectorCreateSchema(BaseSchema):
    """创建选股器"""

    name: str
    description: str | None = None
    rule: ConditionNodeSchema


class SelectorUpdateSchema(BaseSchema):
    """更新选股器"""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    rule: ConditionNodeSchema | None = None


class SelectorSchema(BaseSchema, IDMixin, TimestampMixin):
    """选股器响应"""

    name: str
    description: str | None
    is_active: bool
    rule: ConditionNodeSchema | None = None


class SelectorListItemSchema(BaseSchema, IDMixin, TimestampMixin):
    """选股器列表项"""

    name: str
    description: str | None
    is_active: bool
    result_count: int = 0
    last_result_date: date | None = None
    last_result_count: int | None = None


class SelectorListParams(PaginationParams):
    """选股器列表查询参数"""

    name: str | None = None
    is_active: bool | None = None


class SelectorResultSchema(BaseSchema, IDMixin):
    """选股结果"""

    selector_id: int
    trade_date: date
    stock_codes: list[str]
    count: int
    execution_time: int | None
    created_at: str
    stocks: list[dict] | None = None


class SelectorFieldSchema(BaseSchema, IDMixin):
    """可筛选字段"""

    name: str
    label: str
    field_type: str
    data_type: str
    operators: list[str]
    options: list[dict] | None = None
    unit: str | None = None
    description: str | None = None


class SelectorExecuteResultSchema(BaseSchema):
    """执行选股结果"""

    selector_id: int
    trade_date: date
    stock_codes: list[str]
    count: int
    execution_time: int
    stocks: list[dict] | None = None


class StockBriefSchema(BaseSchema):
    """股票简要信息"""

    stock_code: str
    short_name: str
    industry: str | None
    close: float | None
    change_pct: float | None