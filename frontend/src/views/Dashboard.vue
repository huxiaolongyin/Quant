<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">欢迎回来，交易员</h1>

    <!-- 概览卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div
        class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg"
      >
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

      <div class="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
        <p class="text-gray-500 text-sm mb-1">运行中策略</p>
        <h3 class="text-3xl font-bold text-gray-800">
          3 <span class="text-lg font-normal text-gray-400">/ 5</span>
        </h3>
        <div class="mt-4 flex items-center space-x-2">
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span class="text-sm text-green-600">双均线策略运行中</span>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
        <p class="text-gray-500 text-sm mb-1">数据状态</p>
        <h3 class="text-xl font-bold text-gray-800">已同步至 2023-10-27</h3>
        <button class="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium">
          检查更新 &rarr;
        </button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { dashboardApi } from "@/api/dashboard";
import { Overview } from "@/types/api";
import { onMounted, ref } from "vue";
// =====================================================================
//                       1. 组件定义与 Props
// =====================================================================

// =====================================================================
//                       2. 状态与引用
// =====================================================================
const overview = ref<Overview>({
  totalMarketValue: 0,
  dailyReturn: 0,
  dailyReturnRate: 0,
});

// =====================================================================
//                       3. 计算属性
// =====================================================================

// =====================================================================
//                       4. 方法与逻辑
// =====================================================================
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
// =====================================================================
//                       5. 生命周期与监听
// =====================================================================
onMounted(() => {
  fetchOverview();
});
</script>
