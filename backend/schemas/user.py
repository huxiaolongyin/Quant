from datetime import datetime
from typing import List, Optional

from pydantic import Field

from .base import BaseSchema, IDMixin, TimestampMixin


class PermissionCreate(BaseSchema):
    name: str = Field(..., max_length=50, description="权限名称")
    code: str = Field(..., max_length=100, description="权限编码")
    module: str = Field(..., max_length=50, description="所属模块")
    type: str = Field(default="menu", description="类型: menu/button")
    description: Optional[str] = Field(None, description="描述")
    parent_id: Optional[int] = Field(None, description="父权限ID")
    sort: int = Field(default=0, description="排序")


class PermissionUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=100)
    module: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    parent_id: Optional[int] = Field(None)
    sort: Optional[int] = Field(None)


class PermissionResponse(BaseSchema, IDMixin, TimestampMixin):
    name: str
    code: str
    module: str
    type: str
    description: Optional[str]
    parent_id: Optional[int]
    sort: int


class RoleCreate(BaseSchema):
    name: str = Field(..., max_length=50, description="角色名称")
    code: str = Field(..., max_length=50, description="角色编码")
    description: Optional[str] = Field(None, description="描述")
    status: int = Field(default=1, description="状态")
    sort: int = Field(default=0, description="排序")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


class RoleUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None)
    status: Optional[int] = Field(None)
    sort: Optional[int] = Field(None)
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleResponse(BaseSchema, IDMixin, TimestampMixin):
    name: str
    code: str
    description: Optional[str]
    status: int
    sort: int


class RoleDetailResponse(RoleResponse):
    permissions: List[PermissionResponse] = Field(default_factory=list)


class UserCreate(BaseSchema):
    username: str = Field(..., max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: str = Field(..., max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    status: int = Field(default=1, description="状态")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")


class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=255)
    status: Optional[int] = Field(None)
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")


class UserResponse(BaseSchema, IDMixin, TimestampMixin):
    username: str
    email: str
    phone: Optional[str]
    avatar: Optional[str]
    nickname: Optional[str]
    status: int
    is_superuser: bool
    last_login: Optional[datetime]


class UserDetailResponse(UserResponse):
    roles: List[RoleResponse] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list, description="权限编码列表")


class LoginRequest(BaseSchema):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseSchema):
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class LoginResponse(BaseSchema):
    token: TokenResponse
    user: UserDetailResponse


class PasswordChange(BaseSchema):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UserProfileUpdate(BaseSchema):
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)