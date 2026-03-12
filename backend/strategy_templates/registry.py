from typing import Dict, List, Optional

from .schemas import StrategyCategory, StrategyTemplate, StrategyTemplateListItem


class StrategyTemplateRegistry:
    """策略模板注册中心"""

    _instance: Optional["StrategyTemplateRegistry"] = None
    _templates: Dict[str, StrategyTemplate] = {}

    def __new__(cls) -> "StrategyTemplateRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, template: StrategyTemplate) -> None:
        """注册模板"""
        self._templates[template.id] = template

    def unregister(self, template_id: str) -> bool:
        """注销模板"""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def get(self, template_id: str) -> Optional[StrategyTemplate]:
        """获取模板"""
        return self._templates.get(template_id)

    def list_all(
        self, category: Optional[str] = None
    ) -> List[StrategyTemplateListItem]:
        """获取所有模板列表（不含代码）"""
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return [
            StrategyTemplateListItem(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category,
                tags=t.tags,
                params=t.params,
                is_builtin=t.is_builtin,
            )
            for t in templates
        ]

    def get_full(self, template_id: str) -> Optional[StrategyTemplate]:
        """获取完整模板（含代码）"""
        return self._templates.get(template_id)

    def count(self) -> int:
        """获取模板数量"""
        return len(self._templates)

    def clear(self) -> None:
        """清空所有模板（仅用于测试）"""
        self._templates.clear()


registry = StrategyTemplateRegistry()