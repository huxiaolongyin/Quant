<template>
  <div class="space-y-6">
    <h1 class="page-title">设置</h1>

    <a-tabs v-model:active-key="activeTab" type="line" @change="onTabChange">
      <a-tab-pane v-if="userStore.hasPermission('user')" key="users" title="用户管理">
        <UserManagement />
      </a-tab-pane>
      <a-tab-pane v-if="userStore.hasPermission('role')" key="roles" title="角色管理">
        <RoleManagement />
      </a-tab-pane>
      <a-tab-pane key="notification" title="通知设置">
        <NotificationManagement />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserManagement from './components/UserManagement.vue'
import RoleManagement from './components/RoleManagement.vue'
import NotificationManagement from './components/NotificationManagement.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('users')

const defaultTab = computed(() => {
  if (userStore.hasPermission('user')) return 'users'
  if (userStore.hasPermission('role')) return 'roles'
  return 'notification'
})

function onTabChange(key: string) {
  router.replace({ query: { tab: key } })
}

watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'roles' && userStore.hasPermission('role')) {
      activeTab.value = 'roles'
    } else if (tab === 'users' && userStore.hasPermission('user')) {
      activeTab.value = 'users'
    } else if (tab === 'notification') {
      activeTab.value = 'notification'
    } else {
      activeTab.value = defaultTab.value
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (!route.query.tab && defaultTab.value) {
    router.replace({ query: { tab: defaultTab.value } })
  }
})
</script>