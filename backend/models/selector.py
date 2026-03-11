from enum import Enum
import json

from tortoise import fields, models


class Operator(str, Enum):
    """规则操作符"""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    LIKE = "like"


class LogicType(str, Enum):
    """逻辑类型"""

    AND = "and"
    OR = "or"


class NodeType(str, Enum):
    """节点类型"""

    GROUP = "group"
    CONDITION = "condition"


class FieldType(str, Enum):
    """字段类型"""

    BASIC = "basic"
    QUOTE = "quote"
    INDICATOR = "indicator"


class DataType(str, Enum):
    """数据类型"""

    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"


class SelectorFieldEnum(Enum):
    """选股字段枚举，统一管理字段名、数据库字段、数据类型"""

    EXCHANGE = ("exchange", "exchange_code", DataType.STRING, FieldType.BASIC)
    EXCHANGE_NAME = ("exchange_name", "exchange_name", DataType.STRING, FieldType.BASIC)
    SECTOR = ("sector", "sector", DataType.STRING, FieldType.BASIC)
    INDUSTRY = ("industry", "industry", DataType.STRING, FieldType.BASIC)
    PROVINCE = ("province", "province", DataType.STRING, FieldType.BASIC)
    CITY = ("city", "city", DataType.STRING, FieldType.BASIC)
    SHORT_NAME = ("short_name", "short_name", DataType.STRING, FieldType.BASIC)
    LISTING_DATE = ("listing_date", "listing_date", DataType.DATE, FieldType.BASIC)

    PRICE = ("price", "close", DataType.NUMBER, FieldType.QUOTE)
    OPEN = ("open", "open", DataType.NUMBER, FieldType.QUOTE)
    HIGH = ("high", "high", DataType.NUMBER, FieldType.QUOTE)
    LOW = ("low", "low", DataType.NUMBER, FieldType.QUOTE)
    VOLUME = ("volume", "volume", DataType.NUMBER, FieldType.QUOTE)
    TURNOVER = ("turnover", "turnover", DataType.NUMBER, FieldType.QUOTE)
    CHANGE_PCT = ("change_pct", "change_pct", DataType.NUMBER, FieldType.QUOTE)

    LIMIT_UP_COUNT = ("limit_up_count", "limit_up_count", DataType.NUMBER, FieldType.INDICATOR)
    LIMIT_DOWN_COUNT = ("limit_down_count", "limit_down_count", DataType.NUMBER, FieldType.INDICATOR)
    LIMIT_COUNT = ("limit_count", "limit_count", DataType.NUMBER, FieldType.INDICATOR)
    MA5 = ("ma5", "ma5", DataType.NUMBER, FieldType.INDICATOR)
    MA10 = ("ma10", "ma10", DataType.NUMBER, FieldType.INDICATOR)
    MA20 = ("ma20", "ma20", DataType.NUMBER, FieldType.INDICATOR)

    def __init__(self, field_name: str, db_field: str, data_type: DataType, field_type: FieldType):
        self._field_name = field_name
        self._db_field = db_field
        self._data_type = data_type
        self._field_type = field_type

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def db_field(self) -> str:
        return self._db_field

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @property
    def field_type(self) -> FieldType:
        return self._field_type

    @classmethod
    def get_by_name(cls, name: str) -> "SelectorFieldEnum | None":
        for member in cls:
            if member.field_name == name:
                return member
        return None

    @classmethod
    def get_all_field_names(cls) -> list[str]:
        return [member.field_name for member in cls]

    @classmethod
    def get_by_field_type(cls, field_type: FieldType) -> list["SelectorFieldEnum"]:
        return [member for member in cls if member.field_type == field_type]


class Selector(models.Model):
    """选股器"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # 反向关系：获取根节点
    nodes: fields.ReverseRelation["SelectorNode"]

    class Meta:
        table = "stock_selectors"

    async def get_root_node(self) -> "SelectorNode | None":
        """获取根节点（parent 为空的节点）"""
        return await self.nodes.filter(parent=None).first()


class SelectorNode(models.Model):
    """
    选股器节点 - 树形结构

    示例结构:
    root (AND)
    ├── condition: exchange = "SZ"
    ├── condition: price <= 50
    └── group (OR)
        ├── condition: pe_ratio < 20
        └── condition: pb_ratio < 1.5
    """

    id = fields.IntField(pk=True)
    selector = fields.ForeignKeyField("quant.Selector", related_name="nodes", on_delete=fields.CASCADE)
    parent = fields.ForeignKeyField(
        "quant.SelectorNode",
        related_name="children",
        null=True,
        on_delete=fields.CASCADE,
        description="父节点，null 表示根节点",
    )
    node_type = fields.CharEnumField(NodeType, description="节点类型")
    logic = fields.CharEnumField(LogicType, null=True, description="逻辑运算符（仅 group 类型）")
    field = fields.CharField(max_length=50, null=True, description="字段名，如 price, pe_ratio")
    operator = fields.CharEnumField(Operator, null=True, description="操作符")
    value = fields.TextField(null=True, description="条件值，支持单值/数组/对象")
    sort_order = fields.IntField(default=0, description="排序序号")

    children: fields.ReverseRelation["SelectorNode"]

    class Meta:
        table = "selector_nodes"

    async def get_children(self) -> list["SelectorNode"]:
        return await self.children.all()

    async def get_tree(self) -> dict:
        result = {
            "id": self.id,
            "node_type": self.node_type.value,
        }

        if self.node_type == NodeType.GROUP:
            result["logic"] = self.logic.value if self.logic else None
            result["children"] = [await child.get_tree() for child in await self.get_children()]
        else:
            result["field"] = self.field
            result["operator"] = self.operator.value if self.operator else None
            field_def = SelectorFieldEnum.get_by_name(self.field) if self.field else None
            
            parsed_value = self.value
            if self.value:
                if self.operator in (Operator.IN, Operator.NOT_IN):
                    try:
                        parsed_value = json.loads(self.value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif field_def and field_def.data_type == DataType.NUMBER:
                    try:
                        parsed_value = float(self.value)
                    except (TypeError, ValueError):
                        pass
            
            result["value"] = parsed_value

        return result


class SelectorResult(models.Model):
    """选股结果快照"""

    id = fields.IntField(pk=True)
    selector = fields.ForeignKeyField("quant.Selector", related_name="results", on_delete=fields.CASCADE)
    trade_date = fields.DateField(description="选股日期")
    stock_codes = fields.JSONField(description="结果股票代码列表")
    count = fields.IntField(default=0, description="结果数量")
    execution_time = fields.IntField(null=True, description="执行耗时(ms)")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "selector_results"
        ordering = ["-trade_date"]


class SelectorField(models.Model):
    """可筛选字段定义"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True, description="字段名称")
    label = fields.CharField(max_length=100, description="显示名称")
    field_type = fields.CharField(max_length=20, description="字段类型: basic/quote/indicator")
    data_type = fields.CharField(max_length=20, description="数据类型: string/number/date/boolean")
    operators = fields.JSONField(description="支持的运算符列表")
    options = fields.JSONField(null=True, description="可选值列表(用于下拉选择)")
    unit = fields.CharField(max_length=20, null=True, description="单位: %, 元, 倍")
    description = fields.CharField(max_length=200, null=True, description="字段说明")
    sort_order = fields.IntField(default=0, description="排序")

    class Meta:
        table = "selector_fields"
        ordering = ["sort_order", "name"]


# class SelectorRule(models.Model):
#     """选股规则（单条规则）"""

#     id = fields.IntField(pk=True)
#     selector = fields.ForeignKeyField(
#         "quant.StockSelector", related_name="rules", on_delete=fields.CASCADE
#     )
#     field = fields.CharEnumField(RuleField, description="筛选字段")
#     operator = fields.CharEnumField(RuleOperator, description="操作符")
#     value = fields.JSONField(description="条件值，支持单值/数组/范围")
#     # 时间窗口（用于技术指标类规则）
#     time_window = fields.IntField(null=True, description="时间窗口(天)，如：近15日")
#     is_active = fields.BooleanField(default=True, description="是否启用")
#     description = fields.CharField(max_length=200, null=True, description="规则说明")
#     created_at = fields.DatetimeField(auto_now_add=True)

#     class Meta:
#         table = "selector_rules"
#     def __str__(self):
#         return f"{self.field} {self.operator} {self.value}"
