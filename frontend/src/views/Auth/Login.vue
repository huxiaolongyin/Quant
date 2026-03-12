<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-800"
  >
    <div
      class="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-md p-8 border border-slate-200 dark:border-slate-700 relative"
    >
      <div class="absolute top-4 right-4">
        <a-radio-group
          v-model="themeStore.theme"
          type="button"
          size="mini"
          @change="themeStore.setTheme"
        >
          <a-radio value="light">
            <span class="material-symbols-outlined text-sm">light_mode</span>
          </a-radio>
          <a-radio value="dark">
            <span class="material-symbols-outlined text-sm">dark_mode</span>
          </a-radio>
          <a-radio value="system">
            <span class="material-symbols-outlined text-sm">settings_suggest</span>
          </a-radio>
        </a-radio-group>
      </div>

      <div class="text-center mb-8">
        <div class="flex items-center justify-center gap-3 mb-4">
          <div class="bg-primary rounded-lg w-14 h-14 flex items-center justify-center">
            <span class="material-symbols-outlined text-white text-4xl">insights</span>
          </div>
        </div>
        <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Quant</h1>
        <p class="text-slate-500 dark:text-slate-400 mt-2">Trading Terminal</p>
      </div>

      <a-form :model="form" @submit-success="handleLogin" layout="vertical">
        <a-form-item
          field="username"
          label="用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input v-model="form.username" placeholder="请输入用户名" allow-clear>
            <template #prefix>
              <span class="material-symbols-outlined text-slate-400">person</span>
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          field="password"
          label="密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model="form.password" placeholder="请输入密码" allow-clear>
            <template #prefix>
              <span class="material-symbols-outlined text-slate-400">lock</span>
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            long
            class="!bg-primary hover:!bg-blue-600"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="text-center text-sm text-slate-400 dark:text-slate-500 mt-6">
        默认账户: admin / admin123
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { authApi } from "@/api/auth";
import { useThemeStore } from "@/stores/theme";
import { useUserStore } from "@/stores/user";
import { Message } from "@arco-design/web-vue";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const userStore = useUserStore();
const themeStore = useThemeStore();

const loading = ref(false);
const form = reactive({
  username: "",
  password: "",
});

async function handleLogin() {
  loading.value = true;
  try {
    const res = await authApi.login(form);
    if (res.code === 200 && res.data) {
      userStore.setToken(res.data.token.accessToken, res.data.token.refreshToken);
      userStore.userInfo = res.data.user;
      userStore.permissions = res.data.user.permissions || [];
      Message.success("登录成功");
      router.push("/");
    } else {
      Message.error(res.message || "登录失败");
    }
  } catch (error: any) {
    Message.error(error.response?.data?.detail || "登录失败");
  } finally {
    loading.value = false;
  }
}
</script>
