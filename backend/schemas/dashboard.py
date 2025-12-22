from .base import BaseSchema


class OverView(BaseSchema):
    total_market_value: float
    daily_return: float
    daily_return_rate: float
