from tortoise import fields

from .base import BaseModel, TimestampMixin


class Permission(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, description="权限名称")
    code = fields.CharField(max_length=100, unique=True, description="权限编码")
    module = fields.CharField(max_length=50, description="所属模块")
    type = fields.CharField(max_length=20, default="menu", description="类型: menu/button")
    description = fields.TextField(null=True, description="描述")
    parent_id = fields.IntField(null=True, description="父权限ID")
    sort = fields.IntField(default=0, description="排序")

    class Meta:
        table = "permission"

    def __str__(self):
        return f"{self.name}({self.code})"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, description="角色名称")
    code = fields.CharField(max_length=50, unique=True, description="角色编码")
    description = fields.TextField(null=True, description="描述")
    status = fields.IntField(default=1, description="状态: 0-禁用, 1-启用")
    sort = fields.IntField(default=0, description="排序")

    permissions: fields.ManyToManyRelation["Permission"] = fields.ManyToManyField(
        "quant.Permission",
        through="role_permission",
        related_name="roles",
    )

    class Meta:
        table = "role"

    def __str__(self):
        return f"{self.name}({self.code})"


class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=255, description="密码哈希")
    email = fields.CharField(max_length=100, unique=True, description="邮箱")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    avatar = fields.CharField(max_length=255, null=True, description="头像URL")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    status = fields.IntField(default=1, description="状态: 0-禁用, 1-启用")
    is_superuser = fields.BooleanField(default=False, description="是否超级管理员")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")

    roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField(
        "quant.Role",
        through="user_role",
        related_name="users",
    )

    class Meta:
        table = "user"

    def __str__(self):
        return self.username


class UserRole(BaseModel):
    user = fields.ForeignKeyField("quant.User", related_name="user_roles")
    role = fields.ForeignKeyField("quant.Role", related_name="role_users")

    class Meta:
        table = "user_role"
        unique_together = ("user_id", "role_id")


class RolePermission(BaseModel):
    role = fields.ForeignKeyField("quant.Role", related_name="role_permissions")
    permission = fields.ForeignKeyField("quant.Permission", related_name="permission_roles")

    class Meta:
        table = "role_permission"
        unique_together = ("role_id", "permission_id")
