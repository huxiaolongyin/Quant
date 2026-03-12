<template>
  <header
    class="h-16 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-6 bg-white dark:bg-slate-950/50"
  >
    <div class="flex items-center gap-8">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-emerald-500 text-sm">circle</span>
        <h2 class="text-sm font-bold uppercase tracking-wider">Market Status</h2>
      </div>
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-slate-400">HK:</span>
          <span class="text-xs font-bold text-emerald-500 uppercase">Open</span>
        </div>
        <div
          class="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-6"
        >
          <span class="text-xs font-semibold text-slate-400">US:</span>
          <span class="text-xs font-bold text-rose-500 uppercase">Closed</span>
        </div>
        <div
          class="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-6"
        >
          <span class="text-xs font-semibold text-slate-400">CN:</span>
          <span class="text-xs font-bold text-emerald-500 uppercase">Open</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <div class="relative">
        <span
          class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg"
        >
          search
        </span>
        <input
          class="bg-slate-100 dark:bg-slate-800 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary w-64 text-slate-900 dark:text-slate-100"
          placeholder="Search strategy or ticker..."
          type="text"
        />
      </div>

      <a-dropdown trigger="click" position="br">
        <a-badge :count="unreadCount" :dot="unreadCount > 0" :max-count="99">
          <div class="cursor-pointer hover-surface rounded-lg p-2 transition-colors">
            <span class="material-symbols-outlined text-muted text-xl">
              {{ unreadCount > 0 ? "notifications_active" : "notifications" }}
            </span>
          </div>
        </a-badge>
        <template #content>
          <div class="w-80">
            <div
              class="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700"
            >
              <span class="font-semibold text-slate-900 dark:text-white">消息通知</span>
              <a-button
                type="text"
                size="small"
                @click="markAllRead"
                :disabled="unreadCount === 0"
              >
                全部已读
              </a-button>
            </div>
            <div class="max-h-80 overflow-y-auto">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="px-4 py-3 hover-surface-50 cursor-pointer border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                @click="handleNotificationClick(notification)"
              >
                <div class="flex items-start gap-3">
                  <span
                    class="material-symbols-outlined text-base mt-0.5"
                    :class="getNotificationIconClass(notification.type)"
                  >
                    {{ getNotificationIcon(notification.type) }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span
                        class="text-sm font-medium text-slate-900 dark:text-white truncate"
                      >
                        {{ notification.title }}
                      </span>
                      <span
                        v-if="!notification.read"
                        class="w-2 h-2 rounded-full bg-primary flex-shrink-0"
                      ></span>
                    </div>
                    <p class="text-xs text-muted mt-1 line-clamp-2">
                      {{ notification.content }}
                    </p>
                    <span class="text-xs text-slate-400 mt-1">{{
                      notification.time
                    }}</span>
                  </div>
                </div>
              </div>
              <div v-if="notifications.length === 0" class="empty-state py-8">
                <span class="material-symbols-outlined text-4xl mb-2"
                  >notifications_off</span
                >
                <p class="text-sm">暂无消息</p>
              </div>
            </div>
          </div>
        </template>
      </a-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

interface Notification {
  id: number;
  title: string;
  content: string;
  type: "info" | "warning" | "success" | "error";
  read: boolean;
  time: string;
}

const notifications = ref<Notification[]>([
  {
    id: 1,
    title: "策略运行完成",
    content: '您的策略"均线策略V2"已完成回测，收益率为+15.3%',
    type: "success",
    read: false,
    time: "5分钟前",
  },
  {
    id: 2,
    title: "数据同步提醒",
    content: "港股数据已同步完成，共更新1,234条记录",
    type: "info",
    read: false,
    time: "10分钟前",
  },
  {
    id: 3,
    title: "系统维护通知",
    content: "系统将于今晚22:00-23:00进行维护升级",
    type: "warning",
    read: true,
    time: "1小时前",
  },
]);

const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length);

function markAllRead() {
  notifications.value.forEach((n) => (n.read = true));
}

function handleNotificationClick(notification: Notification) {
  notification.read = true;
}

function getNotificationIcon(type: string): string {
  const icons: Record<string, string> = {
    info: "info",
    warning: "warning",
    success: "check_circle",
    error: "error",
  };
  return icons[type] || "notifications";
}

function getNotificationIconClass(type: string): string {
  const classes: Record<string, string> = {
    info: "text-blue-500",
    warning: "text-amber-500",
    success: "text-emerald-500",
    error: "text-red-500",
  };
  return classes[type] || "text-slate-400";
}
</script>
