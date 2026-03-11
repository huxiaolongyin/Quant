<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Quant Platform</h1>
        <p class="text-gray-500 mt-2">量化交易平台</p>
      </div>

      <a-form :model="form" @submit-success="handleLogin" layout="vertical">
        <a-form-item field="username" label="用户名" :rules="[{ required: true, message: '请输入用户名' }]">
          <a-input v-model="form.username" placeholder="请输入用户名" allow-clear>
            <template #prefix>
              <icon-user />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item field="password" label="密码" :rules="[{ required: true, message: '请输入密码' }]">
          <a-input-password v-model="form.password" placeholder="请输入密码" allow-clear>
            <template #prefix>
              <icon-lock />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading" long>
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="text-center text-sm text-gray-400 mt-6">
        默认账户: admin / admin123
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconUser, IconLock } from '@arco-design/web-vue/es/icon'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const form = reactive({
  username: '',
  password: ''
})

async function handleLogin() {
  loading.value = true
  try {
    const res = await authApi.login(form)
    if (res.code === 200 && res.data) {
      userStore.setToken(
        res.data.token.accessToken,
        res.data.token.refreshToken
      )
      userStore.userInfo = res.data.user
      userStore.permissions = res.data.user.permissions || []
      Message.success('登录成功')
      router.push('/')
    } else {
      Message.error(res.message || '登录失败')
    }
  } catch (error: any) {
    Message.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
</style>