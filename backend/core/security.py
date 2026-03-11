from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.auth import verify_token
from backend.models.user import Permission, Role, User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = credentials.credentials
    user_id = verify_token(token, "access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get_or_none(id=int(user_id)).prefetch_related("roles", "roles__permissions")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def get_user_permissions(user: User) -> List[str]:
    if user.is_superuser:
        return ["*"]

    permissions = set()
    for role in user.roles:
        if role.status == 1:
            for perm in role.permissions:
                permissions.add(perm.code)
    return list(permissions)


class PermissionChecker:
    def __init__(self, permissions: List[str]):
        self.permissions = permissions

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        user_perms = await get_user_permissions(current_user)
        for perm in self.permissions:
            if perm in user_perms or "*" in user_perms:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少权限: {', '.join(self.permissions)}",
        )


def require_permission(*permissions: str):
    return PermissionChecker(list(permissions))
