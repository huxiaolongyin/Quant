from tortoise import fields, models


class Stock(models.Model):
    """股票列表"""

    # 交易所名称	交易所缩写	板块	A股代码	A股代码全称	A股简称	英文名称	公司全称	A股上市日期	所属行业	省份	城市
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

    class Meta:
        table = "stocks"

    def __str__(self):
        return f"{self.full_stock_code} - {self.short_name}"
