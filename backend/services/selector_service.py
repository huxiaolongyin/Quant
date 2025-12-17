from backend.models.selector import (
    LogicType,
    NodeType,
    Operator,
    Selector,
    SelectorNode,
)


class SelectorService:
    """选股器服务 - JSON 输入/输出"""

    @staticmethod
    async def create_from_json(
        name: str, rule: dict, description: str = ""
    ) -> Selector:
        """
        从 JSON 创建选股器

        rule 示例:
        {
            "logic": "and",
            "children": [
                {"field": "exchange", "operator": "eq", "value": "SZ"},
                {"field": "price", "operator": "lte", "value": 50},
                {
                    "logic": "or",
                    "children": [
                        {"field": "pe_ratio", "operator": "lt", "value": 20},
                        {"field": "pb_ratio", "operator": "lt", "value": 1.5}
                    ]
                }
            ]
        }
        """
        selector = await Selector.create(name=name, description=description)
        await SelectorService._create_node(selector, None, rule, 0)
        return selector

    @staticmethod
    async def _create_node(
        selector: Selector, parent: SelectorNode | None, data: dict, order: int
    ) -> SelectorNode:
        """递归创建节点"""
        is_group = "children" in data

        node = await SelectorNode.create(
            selector=selector,
            parent=parent,
            node_type=NodeType.GROUP if is_group else NodeType.CONDITION,
            logic=LogicType(data["logic"]) if is_group else None,
            field=data.get("field"),
            operator=Operator(data["operator"]) if data.get("operator") else None,
            value=data.get("value"),
            sort_order=order,
        )

        if is_group:
            for i, child in enumerate(data.get("children", [])):
                await SelectorService._create_node(selector, node, child, i)

        return node

    @staticmethod
    async def to_json(selector: Selector) -> dict:
        """导出选股器为 JSON"""
        root = await selector.get_root_node()
        return {
            "id": selector.id,
            "name": selector.name,
            "description": selector.description,
            "is_active": selector.is_active,
            "rule": await root.get_tree() if root else None,
        }

    @staticmethod
    async def update_rule(selector: Selector, rule: dict) -> Selector:
        """更新选股规则（删除旧节点，重建新树）"""
        await selector.nodes.all().delete()
        await SelectorService._create_node(selector, None, rule, 0)
        return selector
