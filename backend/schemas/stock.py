from pydantic import BaseModel, Field


class StockBase(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str | None = Field("", description="股票名称")
    holdingNum: int | None = Field(0, description="持有股数")
    costPrice: float | None = Field(0.0, description="成本价")
