"""选股执行引擎"""

import ast
import json
import time
from datetime import date, datetime, timedelta
from typing import Any

from tortoise import connections
from tortoise.expressions import Q

from backend.core.logger import logger
from backend.models.daily import DailyLine
from backend.models.selector import (
    DataType,
    FieldType,
    LogicType,
    NodeType,
    Operator,
    Selector,
    SelectorField,
    SelectorFieldEnum,
    SelectorNode,
    SelectorResult,
)
from backend.models.stock import Stock


class SelectorEngine:

    @classmethod
    async def execute(cls, selector: Selector, trade_date: date | None = None) -> dict:
        start_time = time.time()

        if trade_date is None:
            trade_date = await cls._get_latest_trade_date()

        root_node = await selector.get_root_node()
        if not root_node:
            return {
                "selector_id": selector.id,
                "trade_date": trade_date,
                "stock_codes": [],
                "count": 0,
                "execution_time": 0,
            }

        stock_codes = await cls._evaluate_node(root_node, trade_date)
        execution_time = int((time.time() - start_time) * 1000)

        result = await SelectorResult.create(
            selector_id=selector.id,
            trade_date=trade_date,
            stock_codes=stock_codes,
            count=len(stock_codes),
            execution_time=execution_time,
        )

        stocks = await cls._get_stock_details(stock_codes)

        return {
            "selector_id": selector.id,
            "trade_date": trade_date,
            "stock_codes": stock_codes,
            "count": len(stock_codes),
            "execution_time": execution_time,
            "stocks": stocks,
        }

    @classmethod
    async def _get_latest_trade_date(cls) -> date:
        latest = await DailyLine.all().order_by("-trade_date").first()
        return latest.trade_date if latest else date.today()

    @classmethod
    async def _evaluate_node(cls, node: SelectorNode, trade_date: date) -> list[str]:
        if node.node_type == NodeType.CONDITION:
            return await cls._evaluate_condition(node, trade_date)

        children = await node.children.order_by("sort_order").all()
        if not children:
            return []

        result_sets = []
        for child in children:
            child_codes = await cls._evaluate_node(child, trade_date)
            result_sets.append(set(child_codes))

        if node.logic == LogicType.AND:
            final_codes = set.intersection(*result_sets) if result_sets else set()
        else:
            final_codes = set.union(*result_sets) if result_sets else set()

        return list(final_codes)

    @classmethod
    async def _evaluate_condition(cls, node: SelectorNode, trade_date: date) -> list[str]:
        field = node.field
        operator = node.operator
        raw_value = node.value

        field_enum = SelectorFieldEnum.get_by_name(field) if field else None
        if not field_enum:
            logger.warning(f"Unknown field: {field}")
            return []

        value = cls._parse_value(raw_value, operator, field_enum.data_type)

        if field_enum.field_type == FieldType.BASIC:
            return await cls._filter_basic_field(field_enum.db_field, operator, value)
        elif field_enum.field_type == FieldType.QUOTE:
            return await cls._filter_quote_field(field_enum.db_field, operator, value, trade_date)
        elif field_enum.field_type == FieldType.INDICATOR:
            return await cls._filter_indicator_field(field, operator, value, trade_date)
        else:
            logger.warning(f"Unknown field type: {field_enum.field_type}")
            return []

    @classmethod
    async def _filter_basic_field(cls, db_field: str, operator: Operator, value: Any) -> list[str]:
        q = cls._build_q(db_field, operator, value)
        stocks = await Stock.filter(q).values_list("full_stock_code", flat=True)
        return list(stocks)

    @classmethod
    async def _filter_quote_field(cls, db_field: str, operator: Operator, value: Any, trade_date: date) -> list[str]:
        q = Q(trade_date=trade_date)
        q &= cls._build_q(db_field, operator, value)

        lines = await DailyLine.filter(q).values_list("stock_code", flat=True)
        return list(lines)

    @classmethod
    async def _filter_indicator_field(cls, field: str, operator: Operator, value: Any, trade_date: date) -> list[str]:
        if field == "limit_up_count":
            return await cls._filter_limit_count(trade_date, value, operator, is_up=True)
        elif field == "limit_down_count":
            return await cls._filter_limit_count(trade_date, value, operator, is_up=False)
        elif field == "limit_count":
            return await cls._filter_limit_count_total(trade_date, value, operator)
        elif field in ("ma5", "ma10", "ma20"):
            return await cls._filter_ma(field, operator, value, trade_date)
        return []

    @classmethod
    async def _filter_limit_count(cls, trade_date: date, count: int, operator: Operator, is_up: bool) -> list[str]:
        days = 30
        start_date = trade_date - timedelta(days=days)

        threshold = 1.099 if is_up else 0.901
        cmp_op = ">=" if is_up else "<="

        sql = f"""
        WITH daily_data AS (
            SELECT stock_code, trade_date, close,
                   LAG(close) OVER (PARTITION BY stock_code ORDER BY trade_date) AS prev_close
            FROM stock_daily_line
            WHERE trade_date BETWEEN '{start_date}' AND '{trade_date}'
        ),
        limit_hits AS (
            SELECT stock_code,
                   COUNT(*) FILTER (
                       WHERE prev_close > 0
                       AND close {cmp_op} prev_close * {threshold}
                   ) AS hit_count
            FROM daily_data
            GROUP BY stock_code
        )
        SELECT stock_code FROM limit_hits
        """

        if operator == Operator.GTE:
            sql += f" WHERE hit_count >= {count}"
        elif operator == Operator.GT:
            sql += f" WHERE hit_count > {count}"
        elif operator == Operator.LTE:
            sql += f" WHERE hit_count <= {count}"
        elif operator == Operator.LT:
            sql += f" WHERE hit_count < {count}"
        elif operator == Operator.EQ:
            sql += f" WHERE hit_count = {count}"

        conn = connections.get("default")
        result = await conn.execute_query_dict(sql)
        return [row["stock_code"] for row in result]

    @classmethod
    async def _filter_limit_count_total(cls, trade_date: date, count: int, operator: Operator) -> list[str]:
        days = 30
        start_date = trade_date - timedelta(days=days)

        sql = f"""
        WITH daily_data AS (
            SELECT stock_code, trade_date, close,
                   LAG(close) OVER (PARTITION BY stock_code ORDER BY trade_date) AS prev_close
            FROM stock_daily_line
            WHERE trade_date BETWEEN '{start_date}' AND '{trade_date}'
        ),
        limit_hits AS (
            SELECT stock_code,
                   COUNT(*) FILTER (
                       WHERE prev_close > 0
                       AND (close >= prev_close * 1.099 OR close <= prev_close * 0.901)
                   ) AS hit_count
            FROM daily_data
            GROUP BY stock_code
        )
        SELECT stock_code FROM limit_hits
        """

        if operator == Operator.GTE:
            sql += f" WHERE hit_count >= {count}"
        elif operator == Operator.GT:
            sql += f" WHERE hit_count > {count}"
        elif operator == Operator.LTE:
            sql += f" WHERE hit_count <= {count}"
        elif operator == Operator.LT:
            sql += f" WHERE hit_count < {count}"
        elif operator == Operator.EQ:
            sql += f" WHERE hit_count = {count}"

        conn = connections.get("default")
        result = await conn.execute_query_dict(sql)
        return [row["stock_code"] for row in result]

    @classmethod
    async def _filter_ma(cls, ma_field: str, operator: Operator, value: Any, trade_date: date) -> list[str]:
        days_map = {"ma5": 5, "ma10": 10, "ma20": 20}
        days = days_map.get(ma_field, 5)
        start_date = trade_date - timedelta(days=days + 10)

        sql = f"""
        WITH ma_data AS (
            SELECT stock_code, trade_date, close,
                   AVG(close) OVER (
                       PARTITION BY stock_code
                       ORDER BY trade_date
                       ROWS BETWEEN {days - 1} PRECEDING AND CURRENT ROW
                   ) AS ma
            FROM stock_daily_line
            WHERE trade_date BETWEEN '{start_date}' AND '{trade_date}'
        )
        SELECT stock_code FROM ma_data
        WHERE trade_date = '{trade_date}'
        """

        if operator == Operator.GTE:
            sql += f" AND ma >= {value}"
        elif operator == Operator.GT:
            sql += f" AND ma > {value}"
        elif operator == Operator.LTE:
            sql += f" AND ma <= {value}"
        elif operator == Operator.LT:
            sql += f" AND ma < {value}"
        elif operator == Operator.EQ:
            sql += f" AND ma = {value}"

        conn = connections.get("default")
        result = await conn.execute_query_dict(sql)
        return [row["stock_code"] for row in result]

    @classmethod
    def _parse_value(cls, raw_value: str | None, operator: Operator, data_type: DataType) -> Any:
        """解析存储的值，根据操作符和数据类型返回正确类型"""
        if raw_value is None:
            return raw_value

        if operator in (Operator.IN, Operator.NOT_IN):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

        if data_type == DataType.NUMBER:
            try:
                if "." in str(raw_value):
                    return float(raw_value)
                return int(raw_value)
            except (TypeError, ValueError):
                pass

        return raw_value

    @classmethod
    def _build_q(cls, field: str, operator: Operator, value: Any) -> Q:
        # 处理 IN 和 NOT_IN 时，确保 value 是列表
        if operator in (Operator.IN, Operator.NOT_IN) and isinstance(value, str):
            value = cls._parse_list_value(value)

        if operator == Operator.EQ:
            return Q(**{field: value})
        elif operator == Operator.NE:
            return ~Q(**{field: value})
        elif operator == Operator.GT:
            return Q(**{f"{field}__gt": value})
        elif operator == Operator.GTE:
            return Q(**{f"{field}__gte": value})
        elif operator == Operator.LT:
            return Q(**{f"{field}__lt": value})
        elif operator == Operator.LTE:
            return Q(**{f"{field}__lte": value})
        elif operator == Operator.IN:
            return Q(**{f"{field}__in": value})
        elif operator == Operator.NOT_IN:
            return ~Q(**{f"{field}__in": value})
        elif operator == Operator.CONTAINS:
            return Q(**{f"{field}__icontains": value})
        elif operator == Operator.NOT_CONTAINS:
            return ~Q(**{f"{field}__icontains": value})
        elif operator == Operator.LIKE:
            return Q(**{f"{field}__contains": value})
        return Q()

    @classmethod
    def _parse_list_value(cls, value: str) -> list:
        """将字符串形式的列表转换为真正的列表"""
        # 尝试 JSON 解析（如 '["a", "b"]'）
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass

        # 尝试 ast.literal_eval 解析（如 "['a', 'b']"）
        try:
            result = ast.literal_eval(value)
            if isinstance(result, (list, tuple)):
                return list(result)
        except (ValueError, SyntaxError):
            pass

        # 按逗号分割（如 "a, b, c"）
        return [v.strip() for v in value.split(",") if v.strip()]

    @classmethod
    async def _get_stock_details(cls, stock_codes: list[str]) -> list[dict]:
        if not stock_codes:
            return []

        stocks = await Stock.filter(full_stock_code__in=stock_codes).values("full_stock_code", "short_name", "industry")
        return list(stocks)

    @classmethod
    async def get_field_definitions(cls) -> list[dict]:
        cached = await SelectorField.all().order_by("sort_order")
        if cached:
            return [
                {
                    "id": f.id,
                    "name": f.name,
                    "label": f.label,
                    "field_type": f.field_type,
                    "data_type": f.data_type,
                    "operators": f.operators,
                    "options": f.options,
                    "unit": f.unit,
                    "description": f.description,
                }
                for f in cached
            ]

        default_fields = cls._get_default_field_definitions()
        for i, f in enumerate(default_fields):
            await SelectorField.create(
                name=f["name"],
                label=f["label"],
                field_type=f["field_type"],
                data_type=f["data_type"],
                operators=f["operators"],
                options=f.get("options"),
                unit=f.get("unit"),
                description=f.get("description"),
                sort_order=i,
            )
        return default_fields

    @classmethod
    def _get_default_field_definitions(cls) -> list[dict]:
        return [
            {
                "name": "exchange",
                "label": "交易所",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "in", "not_in"],
                "options": [
                    {"label": "深圳", "value": "SZ"},
                    {"label": "上海", "value": "SH"},
                    {"label": "北京", "value": "BJ"},
                ],
            },
            {
                "name": "sector",
                "label": "板块",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "in", "not_in"],
                "options": [
                    {"label": "主板", "value": "主板"},
                    {"label": "创业板", "value": "创业板"},
                    {"label": "科创板", "value": "科创板"},
                    {"label": "北交所", "value": "北交所"},
                ],
            },
            {
                "name": "industry",
                "label": "行业",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "in", "not_in", "contains", "not_contains"],
            },
            {
                "name": "province",
                "label": "省份",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "in", "not_in", "contains"],
            },
            {
                "name": "city",
                "label": "城市",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "in", "not_in", "contains"],
            },
            {
                "name": "short_name",
                "label": "股票名称",
                "field_type": "basic",
                "data_type": "string",
                "operators": ["eq", "ne", "contains", "not_contains", "like"],
                "description": "支持模糊匹配，如排除ST股: 不包含 ST",
            },
            {
                "name": "price",
                "label": "最新价",
                "field_type": "quote",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte", "between"],
                "unit": "元",
            },
            {
                "name": "volume",
                "label": "成交量",
                "field_type": "quote",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte", "between"],
                "unit": "手",
            },
            {
                "name": "turnover",
                "label": "成交额",
                "field_type": "quote",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte", "between"],
                "unit": "元",
            },
            {
                "name": "limit_up_count",
                "label": "涨停次数(近30日)",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "description": "最近30个交易日内的涨停次数",
            },
            {
                "name": "limit_down_count",
                "label": "跌停次数(近30日)",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "description": "最近30个交易日内的跌停次数",
            },
            {
                "name": "limit_count",
                "label": "涨跌停次数(近30日)",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "description": "最近30个交易日内的涨停或跌停总次数",
            },
            {
                "name": "ma5",
                "label": "5日均线",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "unit": "元",
            },
            {
                "name": "ma10",
                "label": "10日均线",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "unit": "元",
            },
            {
                "name": "ma20",
                "label": "20日均线",
                "field_type": "indicator",
                "data_type": "number",
                "operators": ["eq", "ne", "gt", "gte", "lt", "lte"],
                "unit": "元",
            },
        ]


selector_engine = SelectorEngine()
