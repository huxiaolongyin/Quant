export interface UserInfo {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  nickname?: string
  status: number
  isSuperuser: boolean
  lastLogin?: string
  createdAt: string
  updatedAt: string
  roles: RoleInfo[]
  permissions: string[]
}

export interface RoleInfo {
  id: number
  name: string
  code: string
  description?: string
  status: number
  sort: number
  createdAt: string
  updatedAt: string
}

export interface PermissionInfo {
  id: number
  name: string
  code: string
  module: string
  type: 'menu' | 'button'
  description?: string
  parentId?: number
  sort: number
  createdAt: string
  updatedAt: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenInfo {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export interface LoginResponse {
  token: TokenInfo
  user: UserInfo
}

export interface UserCreateRequest {
  username: string
  password: string
  email: string
  phone?: string
  nickname?: string
  avatar?: string
  status: number
  roleIds: number[]
}

export interface UserUpdateRequest {
  username?: string
  password?: string
  email?: string
  phone?: string
  nickname?: string
  avatar?: string
  status?: number
  roleIds?: number[]
}

export interface RoleCreateRequest {
  name: string
  code: string
  description?: string
  status: number
  sort: number
  permissionIds: number[]
}

export interface RoleUpdateRequest {
  name?: string
  code?: string
  description?: string
  status?: number
  sort?: number
  permissionIds?: number[]
}

export interface PasswordChangeRequest {
  oldPassword: string
  newPassword: string
}

export interface ProfileUpdateRequest {
  nickname?: string
  avatar?: string
  phone?: string
}