<template>
  <aside
    class="w-64 border-r border-divider bg-white dark:bg-slate-950 flex flex-col"
  >
    <div class="p-6 flex items-center gap-3">
      <div class="bg-primary p-1.5 rounded-lg">
        <span class="material-symbols-outlined text-white text-2xl">insights</span>
      </div>
      <div>
        <h1 class="text-slate-900 dark:text-white text-lg font-bold leading-none">
          QuantSystem
        </h1>
        <p class="text-slate-500 dark:text-slate-400 text-xs font-medium">
          Pro Trading Terminal
        </p>
      </div>
    </div>

    <nav class="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="sidebar-nav-item"
        :class="
          isActive(item.path) ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
        "
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <p class="text-sm font-medium">
          {{ item.name }}
        </p>
      </router-link>

      <div class="mt-8 pt-8 border-divider-top">
        <router-link
          v-for="item in settingItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-nav-item"
          :class="
            isActive(item.path) ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
          "
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <p class="text-sm font-medium">
            {{ item.name }}
          </p>
        </router-link>
      </div>
    </nav>

    <div class="p-4 border-divider-top">
      <a-dropdown trigger="click" position="top">
        <div
          class="flex items-center gap-3 p-2 cursor-pointer hover-surface rounded-lg transition-colors"
        >
          <div
            class="bg-primary/20 rounded-full h-10 w-10 flex items-center justify-center overflow-hidden"
          >
            <span class="text-primary font-bold">{{ avatarLetter }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold truncate">
              {{ userStore.userInfo?.nickname || userStore.userInfo?.username }}
            </p>
            <p class="text-xs text-slate-500 truncate">
              {{ userStore.userInfo?.isSuperuser ? "超级管理员" : "普通用户" }}
            </p>
          </div>
          <span class="material-symbols-outlined text-slate-400 text-lg"
            >expand_more</span
          >
        </div>
        <template #content>
          <div class="w-52">
            <div class="dropdown-menu-item" @click="goToProfile">
              <span class="material-symbols-outlined text-base">person</span>
              <span class="text-sm font-medium">个人信息</span>
            </div>
            <div class="px-2 py-2">
              <a-radio-group
                v-model="themeStore.theme"
                type="button"
                size="small"
                class="w-full"
                @change="themeStore.setTheme"
              >
                <a-radio value="light">
                  <span class="material-symbols-outlined text-base">light_mode</span>
                </a-radio>
                <a-radio value="dark">
                  <span class="material-symbols-outlined text-base">dark_mode</span>
                </a-radio>
                <a-radio value="system">
                  <span class="material-symbols-outlined text-base"
                    >settings_suggest</span
                  >
                </a-radio>
              </a-radio-group>
            </div>
            <div class="dropdown-menu-item" @click="handleLogout">
              <span class="material-symbols-outlined text-base">logout</span>
              <span class="text-sm font-medium">退出登录</span>
            </div>
          </div>
        </template>
      </a-dropdown>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { authApi } from "@/api/auth";
import { useThemeStore } from "@/stores/theme";
import { useUserStore } from "@/stores/user";
import { Message } from "@arco-design/web-vue";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const themeStore = useThemeStore();

const avatarLetter = computed(() => {
  const name = userStore.userInfo?.nickname || userStore.userInfo?.username || "";
  return name.charAt(0).toUpperCase();
});

function goToProfile() {}

async function handleLogout() {
  try {
    await authApi.logout();
  } catch {}
  userStore.clearToken();
  Message.success("已退出登录");
  router.push("/login");
}

const menuItems = computed(() => {
  const items = [
    { name: "仪表盘", path: "/", icon: "dashboard" },
    { name: "自选行情", path: "/market/watchlist", icon: "show_chart" },
    { name: "数据同步", path: "/data/sync", icon: "sync" },
    { name: "选股器", path: "/selector/list", icon: "filter_alt" },
    { name: "策略工场", path: "/strategy/list", icon: "code" },
    { name: "回测分析", path: "/strategy/backtest", icon: "history" },
  ];

  if (userStore.hasPermission("user")) {
    items.push({ name: "用户管理", path: "/system/users", icon: "group" });
  }

  return items;
});

const settingItems = computed(() => {
  const items: { name: string; path: string; icon: string }[] = [];

  if (userStore.hasPermission("role")) {
    items.push({ name: "角色管理", path: "/system/roles", icon: "settings" });
  }

  return items;
});

const isActive = (path: string) => {
  if (path === "/") {
    return route.path === "/";
  }
  return route.path.startsWith(path);
};
</script>
