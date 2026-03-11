import { http } from './request'
import type { ApiResponse } from './types'
import type {
  LoginRequest,
  LoginResponse,
  TokenInfo,
  UserInfo,
  PasswordChangeRequest,
  ProfileUpdateRequest
} from '@/types/user'

export const authApi = {
  login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return http.post('/v1/auth/login', data)
  },

  logout(): Promise<ApiResponse<null>> {
    return http.post('/v1/auth/logout')
  },

  refresh(refreshToken: string): Promise<ApiResponse<TokenInfo>> {
    return http.post('/v1/auth/refresh', { refreshToken })
  },

  getMe(): Promise<ApiResponse<UserInfo>> {
    return http.get('/v1/auth/me')
  },

  changePassword(data: PasswordChangeRequest): Promise<ApiResponse<null>> {
    return http.put('/v1/auth/password', data)
  },

  updateProfile(data: ProfileUpdateRequest): Promise<ApiResponse<UserInfo>> {
    return http.put('/v1/auth/profile', data)
  }
}