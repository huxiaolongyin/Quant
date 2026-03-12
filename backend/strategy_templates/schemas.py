from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ParamType(str, Enum):
    """参数类型"""

    INT = "int"
    FLOAT = "float"
    STRING = "str"
    BOOL = "bool"


class StrategyCategory(str, Enum):
    """策略分类"""

    TREND = "trend"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    ARBITRAGE = "arbitrage"


class StrategyParamDef(BaseModel):
    """策略参数定义"""

    name: str = Field(..., description="参数名，如 rsi_period")
    display_name: str = Field(..., description="显示名称，如 RSI周期")
    type: ParamType = Field(..., description="参数类型")
    default: Any = Field(..., description="默认值")
    min: Optional[float] = Field(None, description="最小值")
    max: Optional[float] = Field(None, description="最大值")
    description: str = Field(default="", description="参数说明")

    class Config:
        use_enum_values = True


class StrategyTemplate(BaseModel):
    """策略模板"""

    id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: StrategyCategory = Field(..., description="策略分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    params: List[StrategyParamDef] = Field(default_factory=list, description="可配置参数")
    code: str = Field(..., description="策略代码")
    is_builtin: bool = Field(default=True, description="是否内置模板")

    class Config:
        use_enum_values = True


class StrategyTemplateListItem(BaseModel):
    """模板列表项（不含代码）"""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    params: List[StrategyParamDef]
    is_builtin: bool


class CodeValidateRequest(BaseModel):
    """代码验证请求"""

    code: str = Field(..., description="待验证的策略代码")


class CodeValidateResponse(BaseModel):
    """代码验证响应"""

    is_valid: bool = Field(..., description="是否验证通过")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")


class StrategyFromTemplateRequest(BaseModel):
    """从模板创建策略请求"""

    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="策略名称", max_length=200)
    description: Optional[str] = Field(None, description="策略描述")
    params: dict = Field(default_factory=dict, description="参数值")
    tag_ids: List[str] = Field(default_factory=list, description="标签ID列表")