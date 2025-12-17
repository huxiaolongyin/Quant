from enum import Enum

from tortoise import fields, models


class Operator(str, Enum):
    """规则操作符"""

    EQ = "eq"  # 等于
    NE = "ne"  # 不等于
    GT = "gt"  # 大于
    GTE = "gte"  # 大于等于
    LT = "lt"  # 小于
    LTE = "lte"  # 小于等于
    IN = "in"  # 在列表中
    NOT_IN = "not_in"  # 不在列表中
    BETWEEN = "between"  # 区间
    CONTAINS = "contains"  # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    LIKE = "like"  # 模糊匹配


class LogicType(str, Enum):
    """逻辑类型"""

    AND = "and"
    OR = "or"


class NodeType(str, Enum):
    """节点类型"""

    GROUP = "group"  # 逻辑组（可包含子节点）
    CONDITION = "condition"  # 叶子条件


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
    # 所属选股器
    selector = fields.ForeignKeyField(
        "quant.Selector", related_name="nodes", on_delete=fields.CASCADE
    )

    # 树形结构：自引用
    parent = fields.ForeignKeyField(
        "quant.SelectorNode",
        related_name="children",
        null=True,
        on_delete=fields.CASCADE,
        description="父节点，null 表示根节点",
    )

    # 节点类型
    node_type = fields.CharEnumField(NodeType, description="节点类型")

    # --- GROUP 类型字段 ---
    logic = fields.CharEnumField(
        LogicType, null=True, description="逻辑运算符（仅 group 类型）"
    )

    # --- CONDITION 类型字段 ---
    field = fields.CharField(
        max_length=50, null=True, description="字段名，如 price, pe_ratio"
    )

    operator = fields.CharEnumField(Operator, null=True, description="操作符")

    value = fields.JSONField(null=True, description="条件值，支持单值/数组/对象")

    # 反向关系
    children: fields.ReverseRelation["SelectorNode"]

    class Meta:
        table = "selector_nodes"

    async def get_children(self) -> list["SelectorNode"]:
        """获取子节点"""
        return await self.children.all()

    async def get_tree(self) -> dict:
        """递归构建完整树结构"""
        result = {
            "id": self.id,
            "node_type": self.node_type.value,
        }

        if self.node_type == NodeType.GROUP:
            result["logic"] = self.logic.value if self.logic else None
            result["children"] = [
                await child.get_tree() for child in await self.get_children()
            ]
        else:
            result["field"] = self.field
            result["operator"] = self.operator.value if self.operator else None
            result["value"] = self.value

        return result


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
