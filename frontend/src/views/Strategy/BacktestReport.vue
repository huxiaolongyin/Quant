<template>
  <div class="space-y-6 p-4">
    <div class="card-shadow p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="section-title flex items-center">
          <span class="material-symbols-outlined mr-2">settings</span> 回测配置
        </h3>
        <a-tag color="arcoblue" v-if="isRunning">回测运行中...</a-tag>
      </div>

      <a-form :model="form" layout="vertical" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <a-form-item field="strategyId" label="选择策略" required>
          <a-select v-model="form.strategyId" placeholder="请选择策略脚本" :loading="loadingStrategies">
            <a-option v-for="s in strategies" :key="s.id" :value="s.id" :label="s.name" />
          </a-select>
        </a-form-item>

        <a-form-item field="codes" label="回测标的 (股票/ETF)" required>
          <a-select v-model="form.codes" placeholder="输入代码或名称搜索" multiple allow-search :max-tag-count="2" :options="stockOptions" @search="handleStockSearch" />
        </a-form-item>

        <a-form-item field="dateRange" label="回测区间" required>
          <a-range-picker v-model="form.dateRange" class="w-full" value-format="YYYY-MM-DD" />
        </a-form-item>

        <a-form-item field="initialCapital" label="初始资金 (CNY)">
          <a-input-number v-model="form.initialCapital" :min="10000" :step="10000" mode="button" class="w-full" />
        </a-form-item>

        <div class="md:col-span-4 flex justify-end pt-2 border-t border-slate-200 dark:border-slate-700 mt-2">
          <a-button @click="handleReset" class="mr-3">重置</a-button>
          <a-button type="primary" status="success" :loading="isRunning" @click="startBacktest">
            <template #icon><span class="material-symbols-outlined text-base">play_arrow</span></template>
            开始回测
          </a-button>
        </div>
      </a-form>
    </div>

    <div v-if="result" class="space-y-6 animate-fade-in">
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-2xl font-bold text-slate-800 dark:text-white">{{ result.info.strategyName }}</h2>
          <div class="flex items-center gap-2 text-slate-500 text-sm mt-1">
            <span class="bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded">日线 (1d)</span>
            <span>区间: {{ result.info.period }}</span>
          </div>
        </div>
        <div class="space-x-3">
          <button class="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 text-sm flex items-center gap-2">
            <span class="material-symbols-outlined text-base">download</span> 导出报告
          </button>
          <button class="px-4 py-2 bg-primary rounded-lg text-white hover:bg-blue-600 text-sm">优化参数</button>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="stat-card relative overflow-hidden">
          <div class="text-muted text-xs uppercase font-semibold mb-2">总收益率</div>
          <div class="text-3xl font-bold" :class="getValueColor(result.summary.totalReturns)">
            {{ formatPercent(result.summary.totalReturns) }}
          </div>
          <div class="absolute right-0 bottom-0 opacity-10 transform translate-x-1/4 translate-y-1/4">
            <span class="material-symbols-outlined text-6xl">bar_chart</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="text-muted text-xs uppercase font-semibold mb-2">年化收益</div>
          <div class="text-3xl font-bold text-slate-800 dark:text-white">{{ formatPercent(result.summary.annualizedReturns) }}</div>
        </div>

        <div class="stat-card">
          <div class="text-muted text-xs uppercase font-semibold mb-2">最大回撤</div>
          <div class="text-3xl font-bold text-success">{{ formatPercent(result.summary.maxDrawdown) }}</div>
        </div>

        <div class="stat-card">
          <div class="text-muted text-xs uppercase font-semibold mb-2">夏普比率</div>
          <div class="text-3xl font-bold text-slate-800 dark:text-white">{{ result.summary.sharpeRatio }}</div>
        </div>
      </div>

      <div class="card-shadow p-6 h-96 flex flex-col">
        <h4 class="section-title text-slate-700 dark:text-slate-300 mb-4">收益曲线 (净值 vs 基准)</h4>
        <div class="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-950 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg">
          <div class="text-center text-slate-400">
            <span class="material-symbols-outlined text-5xl mb-2">bar_chart</span>
            <p>此处将渲染 ECharts 收益曲线</p>
            <p class="text-xs mt-1">数据点数: {{ result.charts.dates.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!isRunning" class="empty-state">
      <span class="material-symbols-outlined text-6xl mb-4 text-slate-200">science</span>
      <p>请在上方配置回测参数并点击"开始回测"</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchRunBacktest, fetchSearchStocks, fetchStrategies, type BacktestConfig, type BacktestResult } from "@/api/backtest";
import { Message } from '@arco-design/web-vue';
import { onMounted, reactive, ref } from 'vue';

const loadingStrategies = ref(false);
const isRunning = ref(false);
const strategies = ref<{id: string, name: string}[]>([]);
const stockOptions = ref<{value: string, label: string}[]>([]);

const form = reactive<BacktestConfig>({
  strategyId: '', codes: [], dateRange: ['2023-01-01', '2023-12-31'], initialCapital: 100000, frequency: '1d'
});

const result = ref<BacktestResult | null>(null);

onMounted(async () => {
  loadingStrategies.value = true;
  try {
    strategies.value = await fetchStrategies();
    stockOptions.value = await fetchSearchStocks('');
    if (strategies.value.length > 0) form.strategyId = strategies.value[0].id;
  } finally { loadingStrategies.value = false; }
});

const handleStockSearch = async (value: BacktestConfig) => {
  stockOptions.value = await fetchRunBacktest(value);
};

const handleReset = () => {
  form.codes = []; form.dateRange = ['2023-01-01', '2023-12-31']; form.initialCapital = 100000; result.value = null;
};

const startBacktest = async () => {
  if (!form.strategyId) return Message.warning('请选择策略');
  if (form.codes.length === 0) return Message.warning('请至少选择一支股票');
  if (!form.dateRange || form.dateRange.length !== 2) return Message.warning('请选择回测时间范围');

  isRunning.value = true; result.value = null;
  try {
    const data = await fetchRunBacktest({ ...form });
    result.value = data; Message.success('回测完成');
  } catch (error) { Message.error('回测失败，请稍后重试'); console.error(error); }
  finally { isRunning.value = false; }
};

const formatPercent = (val: number) => `${val > 0 ? '+' : ''}${val.toFixed(2)}%`;
const getValueColor = (val: number) => val > 0 ? 'text-red-500' : val < 0 ? 'text-green-600' : 'text-slate-800 dark:text-white';
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>