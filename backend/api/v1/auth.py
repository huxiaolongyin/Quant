from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from backend.core.auth import create_access_token, create_refresh_token, verify_token
from backend.core.config import Settings
from backend.core.security import get_current_user
from backend.models.user import User
from backend.schemas.base import BaseResponse
from backend.schemas.user import (
    LoginRequest,
    LoginResponse,
    PasswordChange,
    TokenResponse,
    UserDetailResponse,
    UserProfileUpdate,
)
from backend.services.user import UserService

router = APIRouter()


@router.post("/login", response_model=BaseResponse[LoginResponse], summary="用户登录")
async def login(data: LoginRequest):
    user = await UserService.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    await UserService.update_last_login(user.id)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

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

    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=Settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return BaseResponse.success(
        data=LoginResponse(token=token_data, user=user_data), message="登录成功"
    )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    return BaseResponse.success(message="登出成功")


@router.post("/refresh", response_model=BaseResponse[TokenResponse], summary="刷新Token")
async def refresh_token(refresh_token: str):
    user_id = verify_token(refresh_token, "refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user = await UserService.get_by_id(int(user_id))
    if not user or user.status != 1:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return BaseResponse.success(
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=Settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.get("/me", response_model=BaseResponse[UserDetailResponse], summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    permissions = await UserService.get_user_permissions(current_user)

    user_data = UserDetailResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        avatar=current_user.avatar,
        nickname=current_user.nickname,
        status=current_user.status,
        is_superuser=current_user.is_superuser,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        roles=[
            {"id": r.id, "name": r.name, "code": r.code, "status": r.status, "sort": r.sort, "description": r.description, "created_at": r.created_at, "updated_at": r.updated_at}
            for r in current_user.roles
        ],
        permissions=permissions,
    )

    return BaseResponse.success(data=user_data)


@router.put("/password", response_model=BaseResponse, summary="修改密码")
async def change_password(
    data: PasswordChange, current_user: User = Depends(get_current_user)
):
    from backend.core.auth import get_password_hash, verify_password

    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="原密码错误")

    await User.filter(id=current_user.id).update(password=get_password_hash(data.new_password))
    return BaseResponse.success(message="密码修改成功")


@router.put("/profile", response_model=BaseResponse[UserDetailResponse], summary="更新个人资料")
async def update_profile(
    data: UserProfileUpdate, current_user: User = Depends(get_current_user)
):
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await current_user.save()

    return await get_current_user_info(current_user)