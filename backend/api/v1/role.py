from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.security import require_permission
from backend.schemas.base import BaseResponse, PaginatedResponse
from backend.schemas.user import (
    PermissionResponse,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
)
from backend.services.user import PermissionService, RoleService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[RoleResponse],
    summary="获取角色列表",
    dependencies=[Depends(require_permission("role:view"))],
)
async def get_role_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
):
    roles, total = await RoleService.get_list(page=page, page_size=page_size, name=name, status=status)

    role_list = [
        RoleResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            description=r.description,
            status=r.status,
            sort=r.sort,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in roles
    ]

    return PaginatedResponse.create(items=role_list, total=total, page=page, page_size=page_size)


@router.get(
    "/all",
    response_model=BaseResponse[list[RoleResponse]],
    summary="获取所有角色",
)
async def get_all_roles():
    roles = await RoleService.get_all()
    role_list = [
        RoleResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            description=r.description,
            status=r.status,
            sort=r.sort,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in roles
    ]
    return BaseResponse.success(data=role_list)


@router.get(
    "/{role_id}",
    response_model=BaseResponse[RoleDetailResponse],
    summary="获取角色详情",
    dependencies=[Depends(require_permission("role:view"))],
)
async def get_role_detail(role_id: int):
    role = await RoleService.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    role_data = RoleDetailResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        status=role.status,
        sort=role.sort,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                code=p.code,
                module=p.module,
                type=p.type,
                description=p.description,
                parent_id=p.parent_id,
                sort=p.sort,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in role.permissions
        ],
    )

    return BaseResponse.success(data=role_data)


@router.post(
    "",
    response_model=BaseResponse[RoleDetailResponse],
    summary="创建角色",
    dependencies=[Depends(require_permission("role:create"))],
)
async def create_role(data: RoleCreate):
    try:
        role = await RoleService.create(data)
        role_data = RoleDetailResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            status=role.status,
            sort=role.sort,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    code=p.code,
                    module=p.module,
                    type=p.type,
                    description=p.description,
                    parent_id=p.parent_id,
                    sort=p.sort,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in role.permissions
            ],
        )
        return BaseResponse.success(data=role_data, message="角色创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{role_id}",
    response_model=BaseResponse[RoleDetailResponse],
    summary="更新角色",
    dependencies=[Depends(require_permission("role:update"))],
)
async def update_role(role_id: int, data: RoleUpdate):
    try:
        role = await RoleService.update(role_id, data)
        role_data = RoleDetailResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            status=role.status,
            sort=role.sort,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    code=p.code,
                    module=p.module,
                    type=p.type,
                    description=p.description,
                    parent_id=p.parent_id,
                    sort=p.sort,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in role.permissions
            ],
        )
        return BaseResponse.success(data=role_data, message="角色更新成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{role_id}",
    response_model=BaseResponse,
    summary="删除角色",
    dependencies=[Depends(require_permission("role:delete"))],
)
async def delete_role(role_id: int):
    try:
        await RoleService.delete(role_id)
        return BaseResponse.success(message="角色删除成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/permissions/all",
    response_model=BaseResponse[list[PermissionResponse]],
    summary="获取所有权限",
)
async def get_all_permissions():
    permissions = await PermissionService.get_all()
    perm_list = [
        PermissionResponse(
            id=p.id,
            name=p.name,
            code=p.code,
            module=p.module,
            type=p.type,
            description=p.description,
            parent_id=p.parent_id,
            sort=p.sort,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in permissions
    ]
    return BaseResponse.success(data=perm_list)


@router.get(
    "/permissions/by-module",
    response_model=BaseResponse[dict],
    summary="按模块获取权限",
)
async def get_permissions_by_module():
    result = await PermissionService.get_by_module()
    print(result)
    return BaseResponse.success(data=result)
