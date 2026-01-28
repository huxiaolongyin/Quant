from __future__ import annotations

from tortoise import fields

from backend.enums.strategy import (
    ExecutionStatus,
    StrategyStatus,
    TradeType,
    VersionStatus,
)

from .base import BaseModel, TimestampMixin


# fmt: off
class Strategy(BaseModel, TimestampMixin):
    """量化交易策略主表"""

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=200, description="策略名称")
    description = fields.TextField(null=True, description="策略描述")

    # 策略状态
    status = fields.CharEnumField(StrategyStatus, default=StrategyStatus.DRAFT, description="策略状态")
    is_active = fields.BooleanField(default=True, description="是否激活")

    # 当前版本信息
    current_version_id = fields.UUIDField(null=True, description="当前版本ID")
    current_version_number = fields.CharField(max_length=50, null=True, description="当前版本号")
    
    # 统计信息（冗余字段，提升查询性能）
    version_count = fields.IntField(default=0, description="版本数量")
    backtest_count = fields.IntField(default=0, description="回测次数")
    latest_annual_return = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="最新年化收益率(%)")
    latest_sharpe_ratio = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="最新夏普比率")
    latest_win_rate = fields.DecimalField(max_digits=5, decimal_places=2, null=True, description="最新胜率(%)")

    class Meta:
        table = "strategies"
        table_description = "量化交易策略表"
        indexes = [("name", "status")]

    def __str__(self):
        return f"Strategy({self.name})"

    async def get_current_version(self)-> StrategyVersion | None:
        """获取当前版本"""  
        if self.current_version_id:
            return await StrategyVersion.get(id=self.current_version_id)
        return None
    
    async def create_version(self, version_number: str, code: str, description: str = None, **config):
        """创建新版本"""
        # 检查版本号是否已存在
        existing = await StrategyVersion.filter(strategy=self, version_number=version_number).exists()
        
        if existing:
            raise ValueError(f"版本号 {version_number} 已存在")
        version = await StrategyVersion.create(
            strategy=self,
            version_number=version_number,
            version_description=description,
            code=code,
            **config
        )
        self.version_count += 1
        await self.save(update_fields=['version_count'])
        
        return version

    async def set_current_version(self, version_id: str):
        """设置当前版本"""
        version = await StrategyVersion.get(id=version_id, strategy=self)
        self.current_version_id = version_id
        self.current_version_number = version.version_number
        await self.save()
        
        # 更新版本状态
        await StrategyVersion.filter(strategy=self).update(version_status=VersionStatus.ARCHIVED)
        version.version_status = VersionStatus.ACTIVE
        await version.save()

    async def get_version_history(self):
        """获取版本历史"""
        return await StrategyVersion.filter(strategy=self).order_by("-created_at")

    async def get_tags(self) -> list['StrategyTag']:
        """获取策略标签"""
        return await StrategyTag.filter(strategy_relations__strategy=self).order_by("name")

    async def add_tag(self, tag_id: str) -> None:
        """添加标签"""
        # 检查是否已存在
        exists = await StrategyTagRelation.filter(strategy=self, tag_id=tag_id).exists()
        
        if not exists:
            await StrategyTagRelation.create(strategy=self, tag_id=tag_id)

    async def remove_tag(self, tag_id: str) -> None:
        """移除标签"""
        await StrategyTagRelation.filter(strategy=self, tag_id=tag_id).delete() 


class StrategyVersion(BaseModel):
    """策略版本表"""

    id = fields.UUIDField(pk=True)
    strategy = fields.ForeignKeyField("quant.Strategy", related_name="versions", description="关联策略")

    # 版本信息
    version_number = fields.CharField(max_length=50, description="版本号")
    version_description = fields.TextField(null=True, description="版本变更说明")
    version_status = fields.CharEnumField(VersionStatus, default=VersionStatus.DRAFT, description="版本状态")

    # 策略内容
    code = fields.TextField(description="策略代码")

    # 时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "strategy_versions"
        table_description = "策略版本表"
        indexes = [("strategy", "version_status")]
        
    def __str__(self):
        return f"StrategyVersion({self.strategy_id}-{self.version_number})"


class StrategyTag(BaseModel):
    """策略标签模型"""

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=50, unique=True, description="标签名称")
    color = fields.CharField(max_length=20, default="#1890ff", description="标签颜色")
    description = fields.CharField(max_length=200, null=True, description="标签描述")

    # 时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "strategy_tags"
        table_description = "策略标签表"

    def __str__(self):
        return f"StrategyTag({self.name})"


class StrategyTagRelation(BaseModel):
    """策略标签关联表"""

    id = fields.UUIDField(pk=True)
    strategy = fields.ForeignKeyField("quant.Strategy", related_name="tag_relations", description="关联策略")
    tag = fields.ForeignKeyField("quant.StrategyTag", related_name="strategy_relations", description="关联标签")

    # 时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "strategy_tag_relations"
        table_description = "策略标签关联表"
        unique_together = (("strategy", "tag"),)

    def __str__(self):
        return f"StrategyTagRelation({self.strategy_id}-{self.tag_id})"


class StrategyBacktest(BaseModel):
    """策略回测记录模型"""

    id = fields.UUIDField(pk=True)
    strategy = fields.ForeignKeyField("quant.Strategy", related_name="backtests", description="关联策略")
    version = fields.ForeignKeyField("quant.StrategyVersion", related_name="backtests", description="关联版本", null=True)
    
    # 回测基本信息
    name = fields.CharField(max_length=200, description="回测名称")
    start_date = fields.DateField(description="回测开始日期", index=True)
    end_date = fields.DateField(description="回测结束日期", index=True)

    # 资金信息
    initial_capital = fields.DecimalField(max_digits=15, decimal_places=2, description="初始资金")
    final_capital = fields.DecimalField(max_digits=15, decimal_places=2, null=True, description="最终资金")

    # 绩效指标
    total_return = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="总收益率(%)")
    annual_return = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="年化收益率(%)")
    max_drawdown = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="最大回撤(%)")
    sharpe_ratio = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="夏普比率")
    win_rate = fields.DecimalField(max_digits=5, decimal_places=2, null=True, description="胜率(%)")

    # 交易统计
    trade_count = fields.IntField(default=0, description="总交易次数")
    win_count = fields.IntField(default=0, description="盈利交易次数")
    loss_count = fields.IntField(default=0, description="亏损交易次数")

    # 回测状态和结果
    status = fields.CharEnumField(ExecutionStatus, default=ExecutionStatus.PENDING, description="回测状态")
    result_data = fields.JSONField(default=dict, description="详细回测结果数据")
    error_message = fields.TextField(null=True, description="错误信息")

    # 时间字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")

    class Meta:
        table = "strategy_backtests"
        table_description = "策略回测记录表"

    def __str__(self):
        return f"StrategyBacktest({self.name})"


class StrategyBacktestLog(BaseModel):
    """策略回测记录日志"""
    id = fields.UUIDField(pk=True)
    backtest = fields.ForeignKeyField("quant.StrategyBacktest", related_name="logs", description="关联回测记录")

    # 交易基本信息
    trade_type = fields.CharEnumField(TradeType, description="交易类型")
    trade_date = fields.DateField(description="交易日期")
    trade_time = fields.TimeField(null=True, description="交易时间")

    # 价格和数量
    price = fields.DecimalField(max_digits=10, decimal_places=3, description="交易价格")
    quantity = fields.IntField(description="交易数量(股)")
    
    class Meta:
        table = "strategy_backtest_trade_logs"
        table_description = "策略回测交易记录表"
    def __str__(self):
        return f"TradeLog({self.trade_type} {self.symbol} {self.quantity}@{self.price})"
# class StrategyPerformance(BaseModel):
#     """策略绩效快照模型（用于快速查询列表页面数据）"""

#     id = fields.UUIDField(pk=True)
#     strategy = fields.OneToOneField(
#         "quant.Strategy", related_name="performance", description="关联策略"
#     )

#     # 最新绩效数据（来自最近的回测或实盘）
#     latest_return = fields.DecimalField(
#         max_digits=10, decimal_places=4, default=0, description="最新收益率(%)"
#     )
#     latest_win_rate = fields.DecimalField(
#         max_digits=5, decimal_places=2, default=0, description="最新胜率(%)"
#     )

#     # 历史最佳绩效
#     best_return = fields.DecimalField(
#         max_digits=10, decimal_places=4, default=0, description="历史最佳收益率(%)"
#     )
#     best_win_rate = fields.DecimalField(
#         max_digits=5, decimal_places=2, default=0, description="历史最佳胜率(%)"
#     )

#     # 统计数据
#     backtest_count = fields.IntField(default=0, description="回测次数")
#     execution_count = fields.IntField(default=0, description="执行次数")

#     # 更新时间
#     updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

#     class Meta:
#         table = "strategy_performances"
#         table_description = "策略绩效快照表"

#     def __str__(self):
#         return f"StrategyPerformance({self.strategy_id})"
