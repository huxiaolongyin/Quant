<template>
  <div class="space-y-6 p-4">
    <!-- 1. 回测配置面板 -->
    <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-800 flex items-center">
          <icon-settings class="mr-2" /> 回测配置
        </h3>
        <a-tag color="arcoblue" v-if="isRunning">回测运行中...</a-tag>
      </div>

      <a-form
        :model="form"
        layout="vertical"
        class="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <!-- 策略选择 -->
        <a-form-item field="strategyId" label="选择策略" required>
          <a-select
            v-model="form.strategyId"
            placeholder="请选择策略脚本"
            :loading="loadingStrategies"
          >
            <a-option v-for="s in strategies" :key="s.id" :value="s.id" :label="s.name" />
          </a-select>
        </a-form-item>

        <!-- 标的选择 (支持多选) -->
        <a-form-item field="codes" label="回测标的 (股票/ETF)" required>
          <a-select
            v-model="form.codes"
            placeholder="输入代码或名称搜索"
            multiple
            allow-search
            :max-tag-count="2"
            :options="stockOptions"
            @search="handleStockSearch"
          >
          </a-select>
        </a-form-item>

        <!-- 日期范围 -->
        <a-form-item field="dateRange" label="回测区间" required>
          <a-range-picker
            v-model="form.dateRange"
            class="w-full"
            value-format="YYYY-MM-DD"
          />
        </a-form-item>

        <!-- 初始资金 -->
        <a-form-item field="initialCapital" label="初始资金 (CNY)">
          <a-input-number
            v-model="form.initialCapital"
            :min="10000"
            :step="10000"
            mode="button"
            class="w-full"
          />
        </a-form-item>

        <!-- 操作按钮 -->
        <div class="md:col-span-4 flex justify-end pt-2 border-t border-gray-100 mt-2">
          <a-button @click="handleReset" class="mr-3">重置</a-button>
          <a-button
            type="primary"
            status="success"
            :loading="isRunning"
            @click="startBacktest"
          >
            <template #icon><icon-play-arrow /></template>
            开始回测
          </a-button>
        </div>
      </a-form>
    </div>

    <!-- 2. 回测报告 (有结果时显示) -->
    <div v-if="result" class="space-y-6 animate-fade-in">
      <!-- 头部信息 -->
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-2xl font-bold text-gray-800">{{ result.info.strategyName }}</h2>
          <div class="flex items-center gap-2 text-gray-500 text-sm mt-1">
            <span class="bg-gray-100 px-2 py-0.5 rounded">日线 (1d)</span>
            <span>区间: {{ result.info.period }}</span>
          </div>
        </div>
        <div class="space-x-3">
          <button
            class="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm flex items-center gap-2"
          >
            <icon-download /> 导出报告
          </button>
          <button
            class="px-4 py-2 bg-blue-600 rounded-lg text-white hover:bg-blue-700 text-sm"
          >
            优化参数
          </button>
        </div>
      </div>

      <!-- 关键指标 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- 总收益率 -->
        <div
          class="bg-white p-5 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden"
        >
          <div class="text-gray-500 text-xs uppercase font-semibold mb-2">总收益率</div>
          <div
            class="text-3xl font-bold"
            :class="getValueColor(result.summary.totalReturns)"
          >
            {{ formatPercent(result.summary.totalReturns) }}
          </div>
          <!-- 装饰背景 -->
          <div
            class="absolute right-0 bottom-0 opacity-10 transform translate-x-1/4 translate-y-1/4"
          >
            <icon-bar-chart size="80" />
          </div>
        </div>

        <!-- 年化收益 -->
        <div class="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <div class="text-gray-500 text-xs uppercase font-semibold mb-2">年化收益</div>
          <div class="text-3xl font-bold text-gray-800">
            {{ formatPercent(result.summary.annualizedReturns) }}
          </div>
        </div>

        <!-- 最大回撤 -->
        <div class="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <div class="text-gray-500 text-xs uppercase font-semibold mb-2">最大回撤</div>
          <div class="text-3xl font-bold text-green-600">
            {{ formatPercent(result.summary.maxDrawdown) }}
          </div>
        </div>

        <!-- 夏普比率 -->
        <div class="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <div class="text-gray-500 text-xs uppercase font-semibold mb-2">夏普比率</div>
          <div class="text-3xl font-bold text-gray-800">
            {{ result.summary.sharpeRatio }}
          </div>
        </div>
      </div>

      <!-- 图表占位符 -->
      <div
        class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm h-96 flex flex-col"
      >
        <h4 class="text-gray-700 font-bold mb-4">收益曲线 (净值 vs 基准)</h4>
        <div
          class="flex-1 flex items-center justify-center bg-gray-50 border border-dashed rounded-lg"
        >
          <div class="text-center text-gray-400">
            <icon-bar-chart size="48" class="mb-2 mx-auto" />
            <p>此处将渲染 ECharts 收益曲线</p>
            <p class="text-xs mt-1">数据点数: {{ result.charts.dates.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态/欢迎页 -->
    <div v-else-if="!isRunning" class="py-20 text-center text-gray-400">
      <icon-experiment size="64" class="mb-4 text-gray-200" />
      <p>请在上方配置回测参数并点击“开始回测”</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  fetchRunBacktest,
  fetchSearchStocks,
  fetchStrategies,
  type BacktestConfig,
  type BacktestResult
} from "@/api/backtest";
import { Message } from '@arco-design/web-vue';
import {
  IconBarChart,
  IconDownload,
  IconExperiment,
  IconPlayArrow,
  IconSettings
} from '@arco-design/web-vue/es/icon';
import { onMounted, reactive, ref } from 'vue';

// --- 状态定义 ---
const loadingStrategies = ref(false);
const isRunning = ref(false);
const strategies = ref<{id: string, name: string}[]>([]);
const stockOptions = ref<{value: string, label: string}[]>([]);

// 表单数据
const form = reactive<BacktestConfig>({
  strategyId: '',
  codes: [],
  dateRange: ['2023-01-01', '2023-12-31'],
  initialCapital: 100000,
  frequency: '1d'
});

// 回测结果数据
const result = ref<BacktestResult | null>(null);

// --- 方法 ---

// 初始化加载
onMounted(async () => {
  loadingStrategies.value = true;
  try {
    strategies.value = await fetchStrategies();
    stockOptions.value = await fetchSearchStocks(''); // 加载默认推荐股票
    // 默认选中第一个策略
    if (strategies.value.length > 0) {
      form.strategyId = strategies.value[0].id;
    }
  } finally {
    loadingStrategies.value = false;
  }
});

// 搜索股票
const handleStockSearch = async (value: BacktestConfig) => {
  stockOptions.value = await fetchRunBacktest(value);
};

// 重置表单
const handleReset = () => {
  form.codes = [];
  form.dateRange = ['2023-01-01', '2023-12-31'];
  form.initialCapital = 100000;
  result.value = null;
};

// 开始回测
const startBacktest = async () => {
  // 简单校验
  if (!form.strategyId) return Message.warning('请选择策略');
  if (form.codes.length === 0) return Message.warning('请至少选择一支股票');
  if (!form.dateRange || form.dateRange.length !== 2) return Message.warning('请选择回测时间范围');

  isRunning.value = true;
  result.value = null; // 清空旧结果

  try {
    const data = await fetchRunBacktest({ ...form });
    result.value = data;
    Message.success('回测完成');
  } catch (error) {
    Message.error('回测失败，请稍后重试');
    console.error(error);
  } finally {
    isRunning.value = false;
  }
};

// --- 工具函数 ---

const formatPercent = (val: number) => {
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(2)}%`;
};

const getValueColor = (val: number) => {
  if (val > 0) return 'text-red-500';
  if (val < 0) return 'text-green-600';
  return 'text-gray-800';
};
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
