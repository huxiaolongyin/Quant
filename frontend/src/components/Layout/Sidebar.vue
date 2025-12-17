<template>
  <aside
    class="w-64 bg-slate-900 text-white flex flex-col h-full transition-all duration-300"
  >
    <div class="p-6 flex items-center space-x-3 border-b border-slate-800">
      <div class="w-8 h-8 bg-blue-500 rounded flex items-center justify-center font-bold">
        Q
      </div>
      <span class="text-xl font-bold tracking-wider">QuantPro</span>
    </div>

    <nav class="flex-1 overflow-y-auto py-4">
      <ul class="space-y-1 px-3">
        <li v-for="item in menuItems" :key="item.path">
          <!-- 修改了这里：移除了 active-class，改用 :class 动态绑定 -->
          <router-link
            :to="item.path"
            class="flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors"
            :class="[
              isActive(item.path)
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'text-slate-300 hover:text-white hover:bg-slate-800',
            ]"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span>{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="p-4 border-t border-slate-800">
      <div class="flex items-center space-x-3 text-sm text-slate-400">
        <div class="w-2 h-2 rounded-full bg-green-500"></div>
        <span>系统运行正常</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Code, Database, History, LayoutDashboard, TrendingUp } from "lucide-vue-next";
import { useRoute } from "vue-router"; // 1. 引入 useRoute

const route = useRoute(); // 2. 获取当前路由对象

const menuItems = [
  { name: "仪表盘", path: "/", icon: LayoutDashboard },
  { name: "自选行情", path: "/market/watchlist", icon: TrendingUp },
  { name: "数据同步", path: "/data/sync", icon: Database },
  { name: "策略工场", path: "/strategy/list", icon: Code },
  { name: "回测分析", path: "/strategy/backtest", icon: History },
];

// 3. 自定义高亮判断函数
const isActive = (path: string) => {
  // 如果是根路径 '/'，必须完全相等才算激活
  if (path === "/") {
    return route.path === "/";
  }
  // 其他路径（如 /market），只要当前路由以它开头就算激活（保持子菜单高亮）
  return route.path.startsWith(path);
};
</script>
