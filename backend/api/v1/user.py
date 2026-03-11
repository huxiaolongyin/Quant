from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.security import get_current_user, require_permission
from backend.models.user import User
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.user import (
    UserCreate,
    UserDetailResponse,
    UserResponse,
    UserUpdate,
)
from backend.services.user import UserService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="获取用户列表",
    dependencies=[Depends(require_permission("user:view"))],
)
async def get_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    username: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
):
    users, total = await UserService.get_list(
        page=page, page_size=page_size, username=username, status=status
    )

    user_list = [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            phone=u.phone,
            avatar=u.avatar,
            nickname=u.nickname,
            status=u.status,
            is_superuser=u.is_superuser,
            last_login=u.last_login,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]

    return PaginatedResponse.create(
        items=user_list, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{user_id}",
    response_model=BaseResponse[UserDetailResponse],
    summary="获取用户详情",
    dependencies=[Depends(require_permission("user:view"))],
)
async def get_user_detail(user_id: int):
    user = await UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    permissions = await UserService.get_user_permissions(user)

    user_data = UserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        nickname=user.nickname,
        status=user.status,
        is_superuser=user.is_superuser,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[
            {"id": r.id, "name": r.name, "code": r.code, "status": r.status, "sort": r.sort, "description": r.description, "created_at": r.created_at, "updated_at": r.updated_at}
            for r in user.roles
        ],
        permissions=permissions,
    )

    return BaseResponse.success(data=user_data)


@router.post(
    "",
    response_model=BaseResponse[UserDetailResponse],
    summary="创建用户",
    dependencies=[Depends(require_permission("user:create"))],
)
async def create_user(data: UserCreate):
    try:
        user = await UserService.create(data)
        permissions = await UserService.get_user_permissions(user)

        user_data = UserDetailResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            nickname=user.nickname,
            status=user.status,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[
                {"id": r.id, "name": r.name, "code": r.code, "status": r.status, "sort": r.sort, "description": r.description, "created_at": r.created_at, "updated_at": r.updated_at}
                for r in user.roles
            ],
            permissions=permissions,
        )

        return BaseResponse.success(data=user_data, message="用户创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{user_id}",
    response_model=BaseResponse[UserDetailResponse],
    summary="更新用户",
    dependencies=[Depends(require_permission("user:update"))],
)
async def update_user(user_id: int, data: UserUpdate):
    try:
        user = await UserService.update(user_id, data)
        permissions = await UserService.get_user_permissions(user)

        user_data = UserDetailResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            nickname=user.nickname,
            status=user.status,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[
                {"id": r.id, "name": r.name, "code": r.code, "status": r.status, "sort": r.sort, "description": r.description, "created_at": r.created_at, "updated_at": r.updated_at}
                for r in user.roles
            ],
            permissions=permissions,
        )

        return BaseResponse.success(data=user_data, message="用户更新成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{user_id}",
    response_model=BaseResponse,
    summary="删除用户",
    dependencies=[Depends(require_permission("user:delete"))],
)
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    try:
        await UserService.delete(user_id)
        return BaseResponse.success(message="用户删除成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))