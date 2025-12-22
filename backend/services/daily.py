"""日线数据 Service"""

from datetime import date
from typing import Optional

from backend.models.daily import DailyLine

from .base import BaseService


class DailyLineService(BaseService[DailyLine, dict, dict]):
    """日线数据服务"""

    def __init__(self):
        super().__init__(DailyLine)

    async def get_history(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 250,
    ) -> list[DailyLine]:
        """
        获取股票历史日线数据
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
        """
        query = self.model.filter(stock_code=stock_code)
        if start_date:
            query = query.filter(trade_date__gte=start_date)
        if end_date:
            query = query.filter(trade_date__lte=end_date)

        # 先按日期降序取最近的 limit 条，再反转成正序（从旧到新）
        result = await query.order_by("-trade_date").limit(limit).all()
        return result[::-1]


# 单例
daily_line_service = DailyLineService()
