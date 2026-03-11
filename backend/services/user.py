from datetime import datetime, timezone
from typing import List, Optional, Tuple

from tortoise.exceptions import DoesNotExist, IntegrityError

from backend.core.auth import get_password_hash, verify_password
from backend.models.user import Permission, Role, User
from backend.schemas.base import PaginatedData
from backend.schemas.user import (
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)


class UserService:
    @staticmethod
    async def authenticate(username: str, password: str) -> Optional[User]:
        user = await User.get_or_none(username=username).prefetch_related("roles", "roles__permissions")
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        if user.status != 1:
            return None
        return user

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        return await User.get_or_none(id=user_id).prefetch_related("roles", "roles__permissions")

    @staticmethod
    async def get_by_username(username: str) -> Optional[User]:
        return await User.get_or_none(username=username)

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        return await User.get_or_none(email=email)

    @staticmethod
    async def get_list(
        page: int = 1,
        page_size: int = 20,
        username: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[User], int]:
        query = User.all()
        if username:
            query = query.filter(username__icontains=username)
        if status is not None:
            query = query.filter(status=status)

        total = await query.count()
        users = await query.offset((page - 1) * page_size).limit(page_size).prefetch_related("roles")
        return users, total

    @staticmethod
    async def create(data: UserCreate) -> User:
        if await User.get_or_none(username=data.username):
            raise ValueError("用户名已存在")
        if await User.get_or_none(email=data.email):
            raise ValueError("邮箱已存在")

        user = await User.create(
            username=data.username,
            password=get_password_hash(data.password),
            email=data.email,
            phone=data.phone,
            nickname=data.nickname,
            avatar=data.avatar,
            status=data.status,
        )

        if data.role_ids:
            roles = await Role.filter(id__in=data.role_ids)
            await user.roles.add(*roles)

        return await User.get(id=user.id).prefetch_related("roles", "roles__permissions")

    @staticmethod
    async def update(user_id: int, data: UserUpdate) -> User:
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")

        update_data = data.model_dump(exclude_unset=True, exclude={"role_ids", "password"})

        if data.password:
            update_data["password"] = get_password_hash(data.password)

        for field, value in update_data.items():
            setattr(user, field, value)
        await user.save()

        if data.role_ids is not None:
            roles = await Role.filter(id__in=data.role_ids)
            await user.roles.clear()
            await user.roles.add(*roles)

        return await User.get(id=user_id).prefetch_related("roles", "roles__permissions")

    @staticmethod
    async def delete(user_id: int) -> bool:
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        if user.is_superuser:
            raise ValueError("不能删除超级管理员")
        await user.delete()
        return True

    @staticmethod
    async def update_last_login(user_id: int):
        await User.filter(id=user_id).update(last_login=datetime.now(timezone.utc))

    @staticmethod
    async def get_user_permissions(user: User) -> List[str]:
        if user.is_superuser:
            return ["*"]
        permissions = set()
        for role in user.roles:
            if role.status == 1:
                for perm in role.permissions:
                    permissions.add(perm.code)
        return list(permissions)


class RoleService:
    @staticmethod
    async def get_by_id(role_id: int) -> Optional[Role]:
        return await Role.get_or_none(id=role_id).prefetch_related("permissions")

    @staticmethod
    async def get_list(
        page: int = 1, page_size: int = 20, name: Optional[str] = None, status: Optional[int] = None
    ) -> Tuple[List[Role], int]:
        query = Role.all()
        if name:
            query = query.filter(name__icontains=name)
        if status is not None:
            query = query.filter(status=status)

        total = await query.count()
        roles = await query.offset((page - 1) * page_size).limit(page_size)
        return roles, total

    @staticmethod
    async def get_all() -> List[Role]:
        return await Role.filter(status=1).all()

    @staticmethod
    async def create(data: RoleCreate) -> Role:
        if await Role.get_or_none(code=data.code):
            raise ValueError("角色编码已存在")

        role = await Role.create(
            name=data.name,
            code=data.code,
            description=data.description,
            status=data.status,
            sort=data.sort,
        )

        if data.permission_ids:
            permissions = await Permission.filter(id__in=data.permission_ids)
            await role.permissions.add(*permissions)

        return await Role.get(id=role.id).prefetch_related("permissions")

    @staticmethod
    async def update(role_id: int, data: RoleUpdate) -> Role:
        role = await Role.get_or_none(id=role_id)
        if not role:
            raise ValueError("角色不存在")

        update_data = data.model_dump(exclude_unset=True, exclude={"permission_ids"})
        for field, value in update_data.items():
            setattr(role, field, value)
        await role.save()

        if data.permission_ids is not None:
            permissions = await Permission.filter(id__in=data.permission_ids)
            await role.permissions.clear()
            await role.permissions.add(*permissions)

        return await Role.get(id=role_id).prefetch_related("permissions")

    @staticmethod
    async def delete(role_id: int) -> bool:
        role = await Role.get_or_none(id=role_id)
        if not role:
            return False
        if role.code == "admin":
            raise ValueError("不能删除超级管理员角色")
        await role.delete()
        return True


class PermissionService:
    @staticmethod
    async def get_by_id(perm_id: int) -> Optional[Permission]:
        return await Permission.get_or_none(id=perm_id)

    @staticmethod
    async def get_list(
        page: int = 1,
        page_size: int = 20,
        module: Optional[str] = None,
        type: Optional[str] = None,
    ) -> Tuple[List[Permission], int]:
        query = Permission.all()
        if module:
            query = query.filter(module=module)
        if type:
            query = query.filter(type=type)

        total = await query.count()
        permissions = await query.offset((page - 1) * page_size).limit(page_size)
        return permissions, total

    @staticmethod
    async def get_all() -> List[Permission]:
        return await Permission.all().order_by("module", "sort")

    @staticmethod
    async def get_by_module() -> dict:
        permissions = await Permission.all().order_by("module", "sort")
        result = {}
        for perm in permissions:
            if perm.module not in result:
                result[perm.module] = []
            result[perm.module].append(await perm.to_dict())
        return result

    @staticmethod
    async def create(data: PermissionCreate) -> Permission:
        if await Permission.get_or_none(code=data.code):
            raise ValueError("权限编码已存在")

        return await Permission.create(
            name=data.name,
            code=data.code,
            module=data.module,
            type=data.type,
            description=data.description,
            parent_id=data.parent_id,
            sort=data.sort,
        )

    @staticmethod
    async def update(perm_id: int, data: PermissionUpdate) -> Permission:
        permission = await Permission.get_or_none(id=perm_id)
        if not permission:
            raise ValueError("权限不存在")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)
        await permission.save()
        return permission

    @staticmethod
    async def delete(perm_id: int) -> bool:
        permission = await Permission.get_or_none(id=perm_id)
        if not permission:
            return False
        await permission.delete()
        return True

    @staticmethod
    async def init_default_permissions():
        default_permissions = [
            {"name": "用户管理", "code": "user", "module": "system", "type": "menu", "sort": 1},
            {"name": "用户查看", "code": "user:view", "module": "system", "type": "button", "sort": 1},
            {"name": "用户新增", "code": "user:create", "module": "system", "type": "button", "sort": 2},
            {"name": "用户编辑", "code": "user:update", "module": "system", "type": "button", "sort": 3},
            {"name": "用户删除", "code": "user:delete", "module": "system", "type": "button", "sort": 4},
            {"name": "角色管理", "code": "role", "module": "system", "type": "menu", "sort": 2},
            {"name": "角色查看", "code": "role:view", "module": "system", "type": "button", "sort": 1},
            {"name": "角色新增", "code": "role:create", "module": "system", "type": "button", "sort": 2},
            {"name": "角色编辑", "code": "role:update", "module": "system", "type": "button", "sort": 3},
            {"name": "角色删除", "code": "role:delete", "module": "system", "type": "button", "sort": 4},
            {"name": "策略管理", "code": "strategy", "module": "trading", "type": "menu", "sort": 1},
            {"name": "策略查看", "code": "strategy:view", "module": "trading", "type": "button", "sort": 1},
            {"name": "策略新增", "code": "strategy:create", "module": "trading", "type": "button", "sort": 2},
            {"name": "策略编辑", "code": "strategy:update", "module": "trading", "type": "button", "sort": 3},
            {"name": "策略删除", "code": "strategy:delete", "module": "trading", "type": "button", "sort": 4},
            {"name": "选股器", "code": "selector", "module": "trading", "type": "menu", "sort": 2},
            {"name": "选股器查看", "code": "selector:view", "module": "trading", "type": "button", "sort": 1},
            {"name": "选股器新增", "code": "selector:create", "module": "trading", "type": "button", "sort": 2},
            {"name": "选股器编辑", "code": "selector:update", "module": "trading", "type": "button", "sort": 3},
            {"name": "选股器删除", "code": "selector:delete", "module": "trading", "type": "button", "sort": 4},
            {"name": "数据同步", "code": "sync", "module": "data", "type": "menu", "sort": 1},
            {"name": "自选股", "code": "watchlist", "module": "data", "type": "menu", "sort": 2},
        ]

        for perm_data in default_permissions:
            if not await Permission.get_or_none(code=perm_data["code"]):
                await Permission.create(**perm_data)
