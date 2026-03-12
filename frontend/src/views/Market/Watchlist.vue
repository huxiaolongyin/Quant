<template>
  <div class="flex-1 flex overflow-hidden -m-6">
    <section class="flex-1 flex flex-col overflow-hidden bg-white dark:bg-slate-950">
      <div class="flex items-center gap-4 px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <button class="px-4 py-1.5 rounded-full bg-primary text-white text-xs font-bold">自选股</button>
        <button class="px-4 py-1.5 rounded-full hover-surface text-muted text-xs font-medium">科技股</button>
        <button class="px-4 py-1.5 rounded-full hover-surface text-muted text-xs font-medium">指数</button>
        <span class="material-symbols-outlined text-slate-400 text-sm cursor-pointer hover:text-primary">add_circle</span>
        <div class="ml-auto flex gap-2">
          <button @click="handleRefresh(true)" class="p-2 hover-surface rounded-lg text-muted">
            <span class="material-symbols-outlined">refresh</span>
          </button>
          <button @click="openModal()" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm font-medium flex items-center gap-1">
            <span class="material-symbols-outlined text-base">add</span>
            添加
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-auto custom-scrollbar">
        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-slate-50 dark:bg-slate-900 z-10 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th class="px-6 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">代码</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">名称</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">最新价</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">涨跌幅</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">成交量</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">持有数</th>
              <th class="px-6 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">持仓市值</th>
              <th class="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr
              v-for="stock in stocks"
              :key="stock.id"
              @click="showDetail(stock)"
              class="hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
              :class="{ 'bg-primary/5 border-l-4 border-l-primary': currentStock?.id === stock.id }"
            >
              <td class="px-6 py-4 font-bold text-sm">{{ stock.stockCode }}</td>
              <td class="px-4 py-4 text-xs text-slate-500 dark:text-slate-400">{{ stock.shortName }}</td>
              <td class="px-4 py-4 text-sm font-medium text-right font-mono" :class="getColor(getRealtimeData(stock.stockCode)?.changePercent ?? 0)">
                {{ formatPrice(getRealtimeData(stock.stockCode)?.latestPrice) }}
              </td>
              <td class="px-4 py-4 text-right">
                <span
                  class="px-2 py-1 rounded text-xs font-bold"
                  :class="getChangeClass(getRealtimeData(stock.stockCode)?.changePercent ?? 0)"
                >
                  {{ formatChange(getRealtimeData(stock.stockCode)?.changePercent) }}
                </span>
              </td>
              <td class="px-4 py-4 text-xs text-muted">
                {{ formatVolume(getRealtimeData(stock.stockCode)?.volume) }}
              </td>
              <td class="px-4 py-4 text-xs text-right text-muted">
                {{ stock.holdingNum > 0 ? stock.holdingNum.toLocaleString() : "-" }}
              </td>
              <td class="px-6 py-4 text-xs text-right text-muted">
                {{ formatMarketValue(stock, getRealtimeData(stock.stockCode)?.marketValue) }}
              </td>
              <td class="px-4 py-4 text-center">
                <div class="flex justify-center gap-1">
                  <button @click.stop="openModal(stock)" class="p-1.5 hover-surface rounded">
                    <span class="material-symbols-outlined text-base text-muted">edit</span>
                  </button>
                  <a-popconfirm content="确定要删除吗?" @ok="deleteStock(stock.id)">
                    <button @click.stop class="p-1.5 hover-surface rounded">
                      <span class="material-symbols-outlined text-base text-muted">delete</span>
                    </button>
                  </a-popconfirm>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <aside v-if="currentStock" class="w-[420px] flex flex-col border-l border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-950">
      <div class="p-6 overflow-y-auto custom-scrollbar space-y-6">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-2xl font-bold flex items-center gap-2">
              {{ currentStock.shortName }}
              <span class="text-xs font-normal px-1.5 py-0.5 rounded bg-slate-900 text-muted uppercase tracking-tighter">
                {{ currentStock.stockCode }}
              </span>
            </h3>
            <p class="text-sm text-muted">{{ currentStock.stockCode }}</p>
          </div>
          <button @click="currentStock = null" class="text-slate-400 hover:text-slate-600">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="text-right">
          <p class="text-2xl font-mono font-medium" :class="getColor(getRealtimeData(currentStock.stockCode)?.changePercent ?? 0)">
            {{ formatPrice(getRealtimeData(currentStock.stockCode)?.latestPrice) }}
          </p>
          <p class="text-xs font-bold" :class="getColor(getRealtimeData(currentStock.stockCode)?.changePercent ?? 0)">
            {{ formatChangeWithPrice(getRealtimeData(currentStock.stockCode)) }}
          </p>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex gap-2">
              <span class="text-[10px] font-bold text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded uppercase cursor-pointer hover:text-primary">1H</span>
              <span
                @click="handlePeriodChange('daily')"
                class="text-[10px] font-bold cursor-pointer px-1.5 py-0.5 rounded uppercase"
                :class="chartPeriod === 'daily' ? 'text-primary bg-primary/10' : 'text-slate-400 bg-slate-900 hover:text-primary'"
              >D</span>
              <span
                @click="handlePeriodChange('weekly')"
                class="text-[10px] font-bold cursor-pointer px-1.5 py-0.5 rounded uppercase"
                :class="chartPeriod === 'weekly' ? 'text-primary bg-primary/10' : 'text-slate-400 bg-slate-900 hover:text-primary'"
              >W</span>
              <span
                @click="handlePeriodChange('monthly')"
                class="text-[10px] font-bold cursor-pointer px-1.5 py-0.5 rounded uppercase"
                :class="chartPeriod === 'monthly' ? 'text-primary bg-primary/10' : 'text-slate-400 bg-slate-900 hover:text-primary'"
              >M</span>
            </div>
            <div class="flex gap-2">
              <span class="material-symbols-outlined text-sm text-slate-400 cursor-pointer hover:text-primary">add_chart</span>
              <span class="material-symbols-outlined text-sm text-slate-400 cursor-pointer hover:text-primary">settings</span>
            </div>
          </div>

          <div class="h-64 card overflow-hidden">
            <a-spin :loading="chartLoading" class="w-full h-full">
              <KLineChart v-if="chartData" :data="chartData" />
              <div v-else class="empty-state h-full">
                暂无数据
              </div>
            </a-spin>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-700">
            <p class="text-[10px] font-bold text-slate-400 uppercase">MA (5, 10, 20)</p>
            <p class="text-sm font-bold mt-1">--</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-700">
            <p class="text-[10px] font-bold text-slate-400 uppercase">成交量</p>
            <p class="text-sm font-bold mt-1">{{ formatVolume(getRealtimeData(currentStock.stockCode)?.volume) }}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-700">
            <p class="text-[10px] font-bold text-slate-400 uppercase">持仓数量</p>
            <p class="text-sm font-bold mt-1">{{ currentStock.holdingNum?.toLocaleString() || 0 }}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-700">
            <p class="text-[10px] font-bold text-slate-400 uppercase">持仓市值</p>
            <p class="text-sm font-bold text-primary mt-1">{{ formatMarketValue(currentStock, getRealtimeData(currentStock.stockCode)?.marketValue) }}</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4 pt-4 border-t border-slate-700">
          <button class="w-full py-3 bg-danger text-white rounded-lg font-bold text-sm flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-sm">sell</span>
            卖出
          </button>
          <button class="w-full py-3 bg-success text-white rounded-lg font-bold text-sm flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-sm">shopping_cart</span>
            买入
          </button>
        </div>
      </div>
    </aside>

    <a-modal
      v-model:visible="modalVisible"
      :title="isEditMode ? '编辑自选股' : '添加自选股'"
      :ok-loading="submitLoading"
      @ok="handleStock"
      @cancel="modalVisible = false"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item field="stockId" label="股票ID" v-if="!isEditMode">
          <a-select
            v-model="formData.stockId"
            placeholder="请输入股票代码搜索"
            style="width: 100%"
            :options="filteredStockOptions"
            :allow-search="true"
            :filter-option="false"
            @search="handleStockSearch"
            :loading="searchLoading"
          />
        </a-form-item>
        <a-form-item field="holdingNum" label="持有股数">
          <a-input-number
            v-model="formData.holdingNum"
            mode="button"
            :step="100"
            :min="0"
            placeholder="请输入持有数量"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item field="costPrice" label="持仓成本价">
          <a-input-number
            v-model="formData.costPrice"
            :precision="3"
            :min="0"
            placeholder="请输入买入均价"
            style="width: 100%"
          >
            <template #prefix>¥</template>
          </a-input-number>
        </a-form-item>
        <a-form-item field="notes" label="备注">
          <a-textarea
            v-model="formData.notes"
            placeholder="可选备注信息"
            :max-length="200"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { marketApi } from "@/api/market";
import KLineChart from "@/components/Charts/KLineChart.vue";
import type {
  ChartKLineData,
  KlineData,
  KlinePeriod,
  RealtimeQuote,
  WatchlistStock,
} from "@/types/api";
import { Message } from "@arco-design/web-vue";
import { onMounted, onUnmounted, reactive, ref } from "vue";

const loading = ref(false);
const submitLoading = ref(false);
const chartLoading = ref(false);
const stocks = ref<WatchlistStock[]>([]);
const realtimeQuotes = ref<RealtimeQuote[]>([]);

const isEditMode = ref(false);
const modalVisible = ref(false);
const editingId = ref<number | null>(null);
const formData = reactive({
  stockId: undefined as number | undefined,
  holdingNum: 0,
  costPrice: 0,
  notes: "",
});

const defaultQuote = {
  code: "",
  latestPrice: 0,
  preClose: 0,
  change: 0,
  changePercent: 0,
  open: 0,
  high: 0,
  low: 0,
  volume: 0,
  holdingNum: 0,
  marketValue: 0,
  preMarketValue: 0,
  bars: [],
};

const currentStock = ref<WatchlistStock | null>(null);
const chartPeriod = ref<KlinePeriod>("daily");
const chartData = ref<ChartKLineData | null>(null);
const allStockOptions = ref([]);
const filteredStockOptions = ref([]);
const searchLoading = ref(false);

const getColor = (val: number) =>
  val > 0 ? "text-red-500" : val < 0 ? "text-green-500" : "text-slate-900 dark:text-slate-100";

const getChangeClass = (val: number) =>
  val > 0 ? "bg-success/10 text-success" : val < 0 ? "bg-danger/10 text-danger" : "bg-slate-100 text-slate-500";

const getRealtimeData = (stockCode: string) => {
  const result: RealtimeQuote =
    realtimeQuotes.value.find((item) => item.code === stockCode) ?? defaultQuote;
  return result;
};

const formatPrice = (price?: number) => (price ? price.toFixed(2) : "-");

const formatChange = (change?: number) => {
  if (change === undefined) return "-";
  return `${change > 0 ? "+" : ""}${change.toFixed(2)}%`;
};

const formatChangeWithPrice = (data?: RealtimeQuote) => {
  if (!data || !data.latestPrice) return "-";
  const change = data.change;
  const percent = data.changePercent;
  if (change === undefined || percent === undefined) return "-";
  return `${change > 0 ? "+" : ""}${change.toFixed(2)} (${percent > 0 ? "+" : ""}${percent.toFixed(2)}%)`;
};

const formatVolume = (volume?: number) => {
  if (!volume) return "-";
  if (volume >= 100000000) return `${(volume / 100000000).toFixed(2)}亿`;
  if (volume >= 10000) return `${(volume / 10000).toFixed(2)}万`;
  return volume.toString();
};

const formatMarketValue = (record: WatchlistStock, price?: number) => {
  if (!record.holdingNum || !price) return "-";
  return price.toLocaleString("zh-CN", {
    minimumFractionDigits: 0,
  });
};

const transformKlineData = (data: KlineData[]): ChartKLineData => {
  const dates: string[] = [];
  const values: number[][] = [];
  const volumes: number[] = [];

  data.forEach((item) => {
    dates.push(item.tradeDate);
    values.push([
      Number(item.open),
      Number(item.close),
      Number(item.low),
      Number(item.high),
    ]);
    volumes.push(item.volume);
  });

  return { dates, values, volumes };
};

const fetchList = async () => {
  loading.value = true;
  try {
    const res = await marketApi.getList({ page: 1, pageSize: 100 });
    stocks.value = res.data.list;
  } catch (error) {
    Message.error("获取自选股列表失败");
  } finally {
    loading.value = false;
  }
};

const fetchRealtime = async (forceRefresh: Boolean = false) => {
  try {
    realtimeQuotes.value = (await marketApi.getRealtime(forceRefresh)).data;
  } catch (error) {
    console.error("获取实时行情失败", error);
  }
};

const handleRefresh = (forceRefresh: boolean = false) => {
  fetchList();
  fetchRealtime(forceRefresh);
};

const fetchHistory = async (id: number, period: KlinePeriod) => {
  chartLoading.value = true;
  chartData.value = null;

  try {
    const res = await marketApi.getHistory(id, { period, limit: 100 });
    chartData.value = transformKlineData(res.data);
  } catch (error) {
    Message.error("获取历史行情失败");
  } finally {
    chartLoading.value = false;
  }
};

const showDetail = (record: WatchlistStock) => {
  currentStock.value = record;
  chartPeriod.value = "daily";
  fetchHistory(record.id, "daily");
};

const handlePeriodChange = (period: KlinePeriod) => {
  chartPeriod.value = period;
  if (currentStock.value) {
    fetchHistory(currentStock.value.id, period);
  }
};

const openModal = (record?: WatchlistStock) => {
  if (record) {
    isEditMode.value = true;
    editingId.value = record.id;
    formData.stockId = record.stockId;
    formData.holdingNum = record.holdingNum;
    formData.costPrice = Number(record.costPrice);
    formData.notes = record.notes ?? "";
  } else {
    isEditMode.value = false;
    editingId.value = null;
    formData.stockId = undefined;
    formData.holdingNum = 0;
    formData.costPrice = 0;
    formData.notes = "";
  }
  modalVisible.value = true;
};

const handleStock = async () => {
  submitLoading.value = true;
  try {
    if (isEditMode.value && editingId.value) {
      await marketApi.update(editingId.value, {
        holdingNum: formData.holdingNum,
        costPrice: formData.costPrice,
        notes: formData.notes,
      });
      Message.success("更新成功");
    } else {
      if (!formData.stockId) {
        Message.warning("请输入股票ID");
        return;
      }
      await marketApi.create({
        stockId: formData.stockId,
        holdingNum: formData.holdingNum,
        costPrice: formData.costPrice,
        notes: formData.notes,
      });
      Message.success("添加成功");
    }
    modalVisible.value = false;
    handleRefresh(true);
  } catch (error) {
    Message.error(isEditMode.value ? "更新失败" : "添加失败");
  } finally {
    submitLoading.value = false;
  }
};

const deleteStock = async (id: number) => {
  try {
    await marketApi.delete(id);
    Message.success("删除成功");
    if (currentStock.value?.id === id) {
      currentStock.value = null;
    }
    handleRefresh(true);
  } catch (error) {
    Message.error("删除失败");
  }
};

const fethcStockOption = async () => {
  const result: any = await marketApi.getOptions();
  allStockOptions.value = result.data;
};

let searchTimer: number | null = null;
const handleStockSearch = (value: string) => {
  if (searchTimer) window.clearTimeout(searchTimer);

  if (!value) {
    filteredStockOptions.value = [];
    return;
  }

  searchLoading.value = true;
  searchTimer = window.setTimeout(() => {
    const keyword = value.toLowerCase();
    filteredStockOptions.value = allStockOptions.value
      .filter((item: any) => item.label.toLowerCase().includes(keyword))
      .slice(0, 50);
    searchLoading.value = false;
  }, 300);
};

let refreshTimer: number | null = null;

onMounted(() => {
  handleRefresh();
  fethcStockOption();

  refreshTimer = window.setInterval(() => {
    handleRefresh(true);
  }, 5 * 60 * 1000);
});

onUnmounted(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>