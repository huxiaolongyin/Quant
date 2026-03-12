<template>
  <div>
    <h1 class="page-title mb-6">欢迎回来，交易员</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-gradient-to-br from-primary to-blue-600 rounded-xl p-6 text-white shadow-lg">
        <p class="text-blue-100 text-sm mb-1">总市值</p>
        <h3 class="text-3xl font-bold">
          ￥ {{ formatePrice(overview.totalMarketValue) }}
        </h3>
        <div class="mt-4 flex items-center text-sm">
          <span class="bg-white/20 px-2 py-1 rounded">
            {{ formatRate(overview.dailyReturnRate) }} 今日
          </span>
        </div>
      </div>

      <div class="stat-card">
        <p class="text-muted text-sm mb-1">运行中策略</p>
        <h3 class="text-3xl font-bold text-slate-900 dark:text-white">
          3 <span class="text-lg font-normal text-slate-400">/ 5</span>
        </h3>
        <div class="mt-4 flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-success animate-pulse"></span>
          <span class="text-sm text-success">双均线策略运行中</span>
        </div>
      </div>

      <div class="stat-card">
        <p class="text-muted text-sm mb-1">数据状态</p>
        <h3 class="text-xl font-bold text-slate-900 dark:text-white">已同步至 2023-10-27</h3>
        <button class="mt-4 text-sm text-primary hover:text-blue-400 font-medium">
          检查更新 &rarr;
        </button>
      </div>

      <div class="stat-card">
        <p class="text-muted text-sm mb-1">入库股票数</p>
        <h3 class="text-3xl font-bold text-slate-900 dark:text-white">3</h3>
        <div class="mt-4 flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-success animate-pulse"></span>
          <span class="text-sm text-success">双均线策略运行中</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dashboardApi } from "@/api/dashboard";
import { Overview } from "@/types/api";
import { onMounted, ref } from "vue";

const overview = ref<Overview>({
  totalMarketValue: 0,
  dailyReturn: 0,
  dailyReturnRate: 0,
});

const fetchOverview = async () => {
  const result = await dashboardApi.getOverview();
  overview.value = result.data;
};

function formatePrice(price: number) {
  return price.toFixed(2);
}

function formatRate(rate: number) {
  const percent = (rate * 100).toFixed(2);
  return rate >= 0 ? `+${percent}%` : `${percent}%`;
}

onMounted(() => {
  fetchOverview();
});
</script>