import { http } from './request'
import type { ApiResponse, PaginatedResponse } from './types'
import type {
  UserInfo,
  UserCreateRequest,
  UserUpdateRequest,
  RoleInfo,
  RoleCreateRequest,
  RoleUpdateRequest,
  PermissionInfo
} from '@/types/user'

export const userApi = {
  getList(params: {
    page?: number
    pageSize?: number
    username?: string
    status?: number
  }): Promise<PaginatedResponse<UserInfo>> {
    return http.get('/v1/users', params)
  },

  getDetail(id: number): Promise<ApiResponse<UserInfo>> {
    return http.get(`/v1/users/${id}`)
  },

  create(data: UserCreateRequest): Promise<ApiResponse<UserInfo>> {
    return http.post('/v1/users', data)
  },

  update(id: number, data: UserUpdateRequest): Promise<ApiResponse<UserInfo>> {
    return http.put(`/v1/users/${id}`, data)
  },

  delete(id: number): Promise<ApiResponse<null>> {
    return http.delete(`/v1/users/${id}`)
  }
}

export const roleApi = {
  getList(params: {
    page?: number
    pageSize?: number
    name?: string
    status?: number
  }): Promise<PaginatedResponse<RoleInfo>> {
    return http.get('/v1/roles', params)
  },

  getAll(): Promise<ApiResponse<RoleInfo[]>> {
    return http.get('/v1/roles/all')
  },

  getDetail(id: number): Promise<ApiResponse<RoleInfo & { permissions: PermissionInfo[] }>> {
    return http.get(`/v1/roles/${id}`)
  },

  create(data: RoleCreateRequest): Promise<ApiResponse<RoleInfo>> {
    return http.post('/v1/roles', data)
  },

  update(id: number, data: RoleUpdateRequest): Promise<ApiResponse<RoleInfo>> {
    return http.put(`/v1/roles/${id}`, data)
  },

  delete(id: number): Promise<ApiResponse<null>> {
    return http.delete(`/v1/roles/${id}`)
  },

  getAllPermissions(): Promise<ApiResponse<PermissionInfo[]>> {
    return http.get('/v1/roles/permissions/all')
  },

  getPermissionsByModule(): Promise<ApiResponse<Record<string, PermissionInfo[]>>> {
    return http.get('/v1/roles/permissions/by-module')
  }
}