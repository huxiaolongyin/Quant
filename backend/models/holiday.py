"""记录中国节假日的信息"""

from tortoise import fields

from .base import BaseModel, TimestampMixin


class Holiday(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True)
    date = fields.DateField(unique=True, description="节假日日期")
    name = fields.CharField(max_length=50, description="节假日名称")

    class Meta:
        table = "holidays"
