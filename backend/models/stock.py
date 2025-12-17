from tortoise import fields, models


class Stock(models.Model):
    """股票列表"""

    id = fields.IntField(pk=True)  # 主键
    exchange_name = fields.CharField(max_length=50, description="交易所名称")
    exchange_code = fields.CharField(max_length=20, description="交易所缩写")
    sector = fields.CharField(max_length=100, description="板块")
    stock_code = fields.CharField(max_length=20, description="A股代码")
    full_stock_code = fields.CharField(
        max_length=50, unique=True, description="A股代码全称"
    )
    short_name = fields.CharField(max_length=100, description="A股简称")
    english_name = fields.CharField(max_length=200, null=True, description="英文名称")
    company_full_name = fields.CharField(max_length=300, description="公司全称")
    listing_date = fields.DateField(null=True, description="A股上市日期")
    industry = fields.CharField(max_length=200, null=True, description="所属行业")
    province = fields.CharField(max_length=100, null=True, description="省份")
    city = fields.CharField(max_length=100, null=True, description="城市")
    alias_stock_code = fields.CharField(max_length=50, description="A股代码别名")

    class Meta:
        table = "stocks"

    def __str__(self):
        return f"{self.full_stock_code} - {self.short_name}"


# class SelectedStock(models.Model):
#     id = fields.IntField(pk=True)
#     stock = fields.ForeignKeyField(
#         "quant.Stock", related_name="selected_by", on_delete=fields.RESTRICT
#     )
#     holding_num = fields.IntField(default=0, description="持有股数")
#     cost_price = fields.FloatField(default=0.0, description="成本价")

#     class Meta:
#         table = "selected_stock"
#         unique_together = (("stock",),)  # 单用户唯一，目前只限制股票唯一

#     def __str__(self):
#         return f"Selected {self.stock.code} holding {self.holding_num} at {self.cost_price}"
