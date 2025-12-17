"""通用 Schema 基类"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# =====================================================================
#                            工具函数
# =====================================================================


def to_camel_case(string: str) -> str:
    """
    将下划线命名（snake_case）转换为小驼峰命名（camelCase）

    Args:
        string: 下划线分隔的字符串

    Returns:
        小驼峰命名的字符串

    Examples:
        >>> to_camel_case("user_name")
        'userName'
        >>> to_camel_case("created_at")
        'createdAt'
        >>> to_camel_case("id")
        'id'
    """
    components = string.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


def to_snake_case(string: str) -> str:
    """
    将驼峰命名（camelCase）转换为下划线命名（snake_case）

    Args:
        string: 驼峰命名的字符串

    Returns:
        下划线分隔的字符串

    Examples:
        >>> to_snake_case("userName")
        'user_name'
        >>> to_snake_case("createdAt")
        'created_at'
    """
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()


class TimestampMixin(BaseModel):
    """时间戳 Mixin"""

    created_at: datetime
    updated_at: datetime


# =====================================================================
#                           基础配置类
# =====================================================================


class BaseSchema(BaseModel):
    """
    Schema 基类 - 所有 Schema 的父类。

    提供统一的配置，支持 ORM 对象读取、驼峰命名转换等功能。
    - from_attributes: 支持从 ORM 对象读取属性
    - populate_by_name: 允许通过原始字段名或别名赋值
    - alias_generator: 自动将 snake_case 转换为 camelCase（前端友好）
    - str_strip_whitespace: 自动去除字符串首尾空格
    - use_enum_values: 序列化时使用枚举的值而非枚举对象
    - validate_default: 验证默认值的有效性
    - extra: 忽略未定义的额外字段

    Examples:
        定义 Schema::

            class UserSchema(BaseSchema):
                user_name: str  # JSON 序列化后为 "userName"
                email: str
                age: int

        从 ORM 对象创建::

            user_schema = UserSchema.model_validate(user_orm_object)

        从字典创建（支持驼峰或下划线）::

            user_schema = UserSchema(userName="test", email="test@example.com", age=18)
            user_schema = UserSchema(user_name="test", email="test@example.com", age=18)
    """

    model_config = ConfigDict(
        from_attributes=True,  # 支持 ORM 模式：从对象属性读取值
        populate_by_name=True,  # 允许通过字段名或别名赋值
        alias_generator=to_camel_case,  # 字段别名生成器：snake_case -> camelCase
        str_strip_whitespace=True,  # 自动去除字符串首尾空格
        use_enum_values=True,  # 使用枚举值而非枚举实例
        validate_default=True,  # 验证默认值
        extra="ignore",  # 忽略未定义的额外字段
    )


# =====================================================================
#                           通用 Mixin
# =====================================================================


class IDMixin(BaseModel):
    """
    整数 ID 字段 Mixin

    用于包含自增主键 ID 的 Schema，通常用于响应模型。

    Attributes:
        id: 整数类型的主键 ID
    """

    id: int = Field(..., description="主键ID", examples=[1, 100, 999])


class UUIDMixin(BaseModel):
    """
    UUID 字段 Mixin

    用于使用 UUID 作为主键的 Schema。

    Attributes:
        id: UUID 字符串格式的主键
    """

    id: str = Field(
        ...,
        description="UUID 主键",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class TimestampMixin(BaseModel):
    """
    时间戳 Mixin

    包含创建时间和更新时间，适用于大多数数据库模型的响应。
    时间格式由 JSON 编码器控制，默认为 ISO 8601 格式。

    Attributes:
        created_at: 记录创建时间
        updated_at: 记录最后更新时间
    """

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class StatusMixin(BaseModel):
    """
    状态 Mixin

    通用的启用/禁用状态字段。

    Attributes:
        status: 状态值，0-禁用，1-启用
    """

    status: int = Field(default=1, description="状态: 0-禁用, 1-启用", ge=0, le=1)


# =====================================================================
#                         分页相关请求基类
# =====================================================================


class PaginationParams(BaseSchema):
    """
    分页查询参数

    用于接收分页请求参数，提供计算好的 offset 和 limit。

    Attributes:
        page: 页码，从 1 开始
        page_size: 每页条数，默认 20，最大 100

    Computed:
        offset: 数据库查询偏移量 = (page - 1) * page_size
        limit: 等同于 page_size

    Examples:
        @router.get("/users")
        async def list_users(
            pagination: PaginationParams = Depends()
        ):
            users = await db.query(User).offset(pagination.offset).limit(pagination.limit)
            ...
    """

    page: int = Field(default=1, ge=1, description="页码（从1开始）", examples=[1])
    page_size: int = Field(
        default=20, ge=1, le=100, description="每页条数（最大100）", examples=[20]
    )

    @computed_field
    @property
    def offset(self) -> int:
        """
        计算数据库查询偏移量

        Returns:
            偏移量 = (当前页码 - 1) * 每页条数
        """
        return (self.page - 1) * self.page_size

    @computed_field
    @property
    def limit(self) -> int:
        """
        返回查询限制数量（等同于 page_size）

        Returns:
            每页条数
        """
        return self.page_size


class SortParams(BaseSchema):
    """
    排序参数

    用于接收排序请求参数。

    Attributes:
        sort_by: 排序字段名（应与数据库字段对应）
        sort_order: 排序方向，asc（升序）或 desc（降序）

    Examples:
        @router.get("/users")
        async def list_users(sort: SortParams = Depends()):
            query = select(User)
            if sort.sort_by:
                column = getattr(User, sort.sort_by)
                query = query.order_by(column.desc() if sort.sort_order == "desc" else column)
            ...
    """

    sort_by: Optional[str] = Field(
        default=None, description="排序字段", examples=["created_at"]
    )
    sort_order: Optional[str] = Field(
        default="desc", description="排序方向: asc-升序, desc-降序", examples=["desc"]
    )

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: Optional[str]) -> Optional[str]:
        """验证排序方向只能是 asc 或 desc"""
        if v is not None and v.lower() not in ("asc", "desc"):
            raise ValueError("排序方向只能是 asc 或 desc")
        return v.lower() if v else "desc"


# =====================================================================
#                           响应基类
# =====================================================================

# 泛型类型变量，用于响应数据的类型提示
T = TypeVar("T")


# ============ 响应 ============
class BaseResponse(BaseSchema, Generic[T]):
    """
    统一 API 响应格式

    所有接口响应都应使用此格式，确保前端可以统一处理。

    Attributes:
        code: 业务状态码，200 表示成功，其他表示各类错误
        message: 响应消息，成功时为 "success"，失败时为错误描述
        data: 响应数据，泛型支持任意类型

    Class Methods:
        success: 快速创建成功响应
        error: 快速创建错误响应

    Examples:
        # 方式1：直接实例化
        return BaseResponse(data={"id": 1, "name": "test"})

        # 方式2：使用类方法
        return BaseResponse.success(data=user_dict)
        return BaseResponse.error(message="用户不存在", code=404)

        # 方式3：带类型提示（推荐用于文档生成）
        return BaseResponse[UserSchema](data=user)
    """

    code: int = Field(default=200, description="业务状态码: 200-成功", examples=[200])
    message: str = Field(
        default="success", description="响应消息", examples=["success"]
    )
    data: Optional[T] = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "BaseResponse[T]":
        """
        创建成功响应

        Args:
            data: 响应数据
            message: 成功消息，默认为 "success"

        Returns:
            ApiResponse 实例
        """
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(
        cls, message: str = "error", code: int = 400, data: T = None
    ) -> "BaseResponse[T]":
        """
        创建错误响应

        Args:
            message: 错误消息
            code: 错误码，默认 400
            data: 附加数据（可选）

        Returns:
            ApiResponse 实例
        """
        return cls(code=code, message=message, data=data)


class PaginatedData(BaseSchema, Generic[T]):
    """
    分页数据结构

    用于包装分页查询结果，包含数据列表和分页元信息。

    Attributes:
        list: 当前页的数据列表
        total: 符合条件的总记录数
        page: 当前页码
        page_size: 每页条数

    Computed:
        pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页

    Examples:
        paginated = PaginatedData.create(
            items=users,
            total=100,
            page=1,
            page_size=20
        )
        print(paginated.pages)     # 5
        print(paginated.has_next)  # True
    """

    list: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, ge=0, description="总记录数", examples=[100])
    page: int = Field(default=1, ge=1, description="当前页码", examples=[1])
    page_size: int = Field(default=20, ge=1, description="每页条数", examples=[20])

    @computed_field
    @property
    def pages(self) -> int:
        """
        计算总页数

        Returns:
            总页数，向上取整
        """
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @computed_field
    @property
    def has_next(self) -> bool:
        """
        是否有下一页

        Returns:
            当前页码 < 总页数 时返回 True
        """
        return self.page < self.pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        """
        是否有上一页

        Returns:
            当前页码 > 1 时返回 True
        """
        return self.page > 1

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedData[T]":
        """
        创建分页数据的工厂方法

        Args:
            items: 当前页的数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页条数

        Returns:
            PaginatedData 实例
        """
        return cls(list=items, total=total, page=page, page_size=page_size)


class PaginatedResponse(BaseResponse[PaginatedData[T]], Generic[T]):
    """
    分页响应

    统一的分页接口响应格式，data 字段为 PaginatedData 类型。

    Examples:
        @router.get("/users", response_model=PaginatedResponse[UserSchema])
        async def list_users(params: PaginationParams = Depends()):
            users, total = await user_service.get_list(params)
            return PaginatedResponse.create(
                items=users,
                total=total,
                page=params.page,
                page_size=params.page_size
            )
    """

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "success",
    ) -> "PaginatedResponse[T]":
        """
        创建分页响应的工厂方法

        Args:
            items: 当前页的数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页条数
            message: 响应消息

        Returns:
            PaginatedResponse 实例
        """
        return cls(
            code=200,
            message=message,
            data=PaginatedData.create(items, total, page, page_size),
        )
