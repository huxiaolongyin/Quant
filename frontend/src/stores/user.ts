import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, RoleInfo } from '@/types/user'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const userInfo = ref<UserInfo | null>(null)
  const permissions = ref<string[]>([])

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const isSuperUser = computed(() => userInfo.value?.isSuperuser ?? false)

  function setToken(accessToken: string, refresh?: string) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem('refreshToken', refresh)
    }
  }

  function clearToken() {
    token.value = null
    refreshToken.value = null
    userInfo.value = null
    permissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function fetchUserInfo() {
    try {
      const res = await authApi.getMe()
      if (res.code === 200 && res.data) {
        userInfo.value = res.data
        permissions.value = res.data.permissions || []
        return true
      }
      return false
    } catch {
      clearToken()
      return false
    }
  }

  function hasPermission(perm: string | string[]): boolean {
    if (isSuperUser.value) return true
    if (Array.isArray(perm)) {
      return perm.some(p => permissions.value.includes(p))
    }
    return permissions.value.includes(perm)
  }

  function hasAllPermissions(perms: string[]): boolean {
    if (isSuperUser.value) return true
    return perms.every(p => permissions.value.includes(p))
  }

  return {
    token,
    refreshToken,
    userInfo,
    permissions,
    isLoggedIn,
    isSuperUser,
    setToken,
    clearToken,
    fetchUserInfo,
    hasPermission,
    hasAllPermissions
  }
})