<template>
  <header
    class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10"
  >
    <h2 class="text-lg font-semibold text-gray-700">
      {{ $route.meta.title || "Quant Platform" }}
    </h2>

    <div class="flex items-center space-x-4">
      <div class="text-right mr-4">
        <div class="text-xs text-gray-500">可用资金</div>
        <div class="text-sm font-bold text-gray-800">¥ 1,240,500.00</div>
      </div>

      <a-dropdown>
        <div class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 rounded-lg px-3 py-2">
          <div
            class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold border border-blue-200"
          >
            {{ avatarLetter }}
          </div>
          <div class="text-sm">
            <div class="font-medium text-gray-900">{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</div>
            <div class="text-xs text-gray-500">{{ userStore.userInfo?.isSuperuser ? '超级管理员' : '普通用户' }}</div>
          </div>
        </div>
        <template #content>
          <a-doption @click="goToProfile">
            <template #icon><icon-user /></template>
            个人信息
          </a-doption>
          <a-doption @click="handleLogout">
            <template #icon><icon-export /></template>
            退出登录
          </a-doption>
        </template>
      </a-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconUser, IconExport } from '@arco-design/web-vue/es/icon'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const avatarLetter = computed(() => {
  const name = userStore.userInfo?.nickname || userStore.userInfo?.username || ''
  return name.charAt(0).toUpperCase()
})

function goToProfile() {
  // TODO: 跳转到个人信息页面
}

async function handleLogout() {
  try {
    await authApi.logout()
  } catch {
    // ignore
  }
  userStore.clearToken()
  Message.success('已退出登录')
  router.push('/login')
}
</script>