<template>
  <div class="p-6">
    <a-card
      class="rounded-xl shadow-sm border-gray-100"
      :bordered="false"
      title="自选股列表"
    >
      <template #extra>
        <a-space>
          <a-button @click="handleRefresh(true)">
            <template #icon><icon-refresh /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="openModal()">
            <template #icon><icon-plus /></template>
            添加
          </a-button>
        </a-space>
      </template>

      <a-table
        :data="stocks"
        :loading="loading"
        :pagination="false"
        :bordered="{ wrapper: false, cell: false }"
        row-key="id"
        class="mt-2"
        :hoverable="true"
      >
        <template #columns>
          <a-table-column title="代码" data-index="stockCode">
            <template #cell="{ record }">
              <span class="font-mono text-gray-600 font-bold">
                {{ record.stockCode }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="名称" data-index="shortName">
            <template #cell="{ record }">
              <span class="font-medium text-gray-800">
                {{ record.shortName }}
              </span>
            </template>
          </a-table-column>

          <a-table-column title="最新价" data-index="price" align="right">
            <template #cell="{ record }">
              <span
                class="font-mono font-medium text-base"
                :class="getColor(getRealtimeData(record.stockCode)?.latestPrice ?? 0)"
              >
                {{ formatPrice(getRealtimeData(record.stockCode)?.latestPrice) }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="涨跌幅" data-index="change" align="right">
            <template #cell="{ record }">
              <span
                class="font-mono font-medium"
                :class="getColor(getRealtimeData(record.stockCode)?.changePercent ?? 0)"
              >
                {{ formatChange(getRealtimeData(record.stockCode)?.changePercent) }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="成交量" data-index="volume" align="right">
            <template #cell="{ record }">
              <span class="text-gray-500 text-sm">
                {{ formatVolume(getRealtimeData(record.stockCode)?.volume) }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="持有数" data-index="holdingNum" align="right">
            <template #cell="{ record }">
              <span class="text-gray-800 font-mono">
                {{ record.holdingNum > 0 ? record.holdingNum.toLocaleString() : "-" }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="持仓市值" align="right">
            <template #cell="{ record }">
              <span class="text-gray-800 font-mono font-medium">
                {{
                  formatMarketValue(
                    record,
                    getRealtimeData(record.stockCode)?.marketValue
                  )
                }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="操作" align="center" :width="240">
            <template #cell="{ record }">
              <a-space>
                <a-button
                  type="text"
                  status="success"
                  size="small"
                  @click="showDetail(record)"
                >
                  <template #icon><icon-bar-chart /></template>
                  分析
                </a-button>
                <a-button
                  type="text"
                  status="normal"
                  size="small"
                  @click="openModal(record)"
                >
                  <template #icon><icon-edit /></template>
                  编辑
                </a-button>
                <a-popconfirm content="确定要删除吗?" @ok="deleteStock(record.id)">
                  <a-button type="text" status="danger" size="small">
                    <template #icon><icon-delete /></template>
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

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

    <!-- 详情 Drawer -->
    <a-drawer
      :width="900"
      :visible="detailVisible"
      @cancel="detailVisible = false"
      :footer="false"
      unmountOnClose
    >
      <template #title>
        <div v-if="currentStock" class="flex items-center space-x-3">
          <span class="text-xl font-bold text-gray-800">{{
            currentStock.shortName
          }}</span>
          <span class="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded font-mono">
            {{ currentStock.stockCode }}
          </span>
          <span
            class="font-mono font-bold"
            :class="getColor(getRealtimeData(currentStock.stockCode)?.changePercent ?? 0)"
          >
            {{ formatPrice(getRealtimeData(currentStock.stockCode)?.marketValue) }}
            ({{ formatChange(getRealtimeData(currentStock.stockCode)?.changePercent) }})
          </span>
        </div>
      </template>

      <div class="h-full flex flex-col">
        <!-- 周期切换 -->
        <a-tabs
          type="rounded"
          v-model:active-key="chartPeriod"
          @change="handlePeriodChange"
        >
          <a-tab-pane key="daily" title="日K"></a-tab-pane>
          <a-tab-pane key="weekly" title="周K"></a-tab-pane>
          <a-tab-pane key="monthly" title="月K"></a-tab-pane>
        </a-tabs>

        <!-- ECharts 组件容器 -->
        <div
          class="flex-1 bg-white rounded-lg border border-gray-200 mt-4 p-2 min-h-[400px]"
        >
          <a-spin :loading="chartLoading" class="w-full h-full">
            <KLineChart v-if="chartData" :data="chartData" />
            <div
              v-else
              class="h-full flex items-center justify-center text-gray-400 min-h-[400px]"
            >
              暂无数据
            </div>
          </a-spin>
        </div>

        <!-- 盘口信息 -->
        <!-- <div v-if="currentStock" class="mt-4 grid grid-cols-2 gap-4 h-48">
          <div class="bg-red-50 p-3 rounded border border-red-100 flex flex-col justify-between">
            <div class="text-xs text-red-500 font-bold border-b border-red-200 pb-1">
              卖盘 (Ask)
            </div>
            <div v-for="i in 5" :key="`ask-${i}`" class="flex justify-between text-xs">
              <span class="text-gray-500">卖{{ 6 - i }}</span>
              <span class="font-mono text-red-600">
                {{
                  (
                    (getRealtimeData(currentStock.stockCode)?.price ?? 0) +
                    (6 - i) * 0.02
                  ).toFixed(2)
                }}
              </span>
              <span class="font-mono text-gray-600">
                {{ Math.floor(Math.random() * 200) }}
              </span>
            </div>
          </div>
          <div class="bg-green-50 p-3 rounded border border-green-100 flex flex-col justify-between">
            <div class="text-xs text-green-500 font-bold border-b border-green-200 pb-1">
              买盘 (Bid)
            </div>
            <div v-for="i in 5" :key="`bid-${i}`" class="flex justify-between text-xs">
              <span class="text-gray-500">买{{ i }}</span>
              <span class="font-mono text-green-600">
                {{
                  (
                    (getRealtimeData(currentStock.shortName)?.price ?? 0) -
                    i * 0.02
                  ).toFixed(2)
                }}
              </span>
              <span class="font-mono text-gray-600">
                {{ Math.floor(Math.random() * 200) }}
              </span>
            </div>
          </div>
        </div> -->
      </div>
    </a-drawer>
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
import {
  IconBarChart,
  IconDelete,
  IconEdit,
  IconPlus,
  IconRefresh,
} from "@arco-design/web-vue/es/icon";
import { onMounted, onUnmounted, reactive, ref } from "vue";

// =====================================================================
//                       1. 组件定义与 Props
// =====================================================================

// =====================================================================
//                       2. 状态与引用
// =====================================================================
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
const detailVisible = ref(false);
const currentStock = ref<WatchlistStock | null>(null);
const chartPeriod = ref<KlinePeriod>("daily");
const chartData = ref<ChartKLineData | null>(null);
const allStockOptions = ref([]); // 存储所有选项
const filteredStockOptions = ref([]); // 展示的选项
const searchLoading = ref(false);

// =====================================================================
//                       3. 计算属性
// =====================================================================

// =====================================================================
//                       4. 方法与逻辑
// =====================================================================
// 设置颜色
const getColor = (val: number) =>
  val > 0 ? "text-red-500" : val < 0 ? "text-green-500" : "text-gray-900";

const getRealtimeData = (stockCode: string) => {
  const result: RealtimeQuote =
    realtimeQuotes.value.find((item) => item.code === stockCode) ?? defaultQuote;
  return result;
};

// 格式化价格
const formatPrice = (price?: number) => (price ? price.toFixed(2) : "-");

const formatChange = (change?: number) => {
  if (change === undefined) return "-";
  return `${change > 0 ? "+" : ""}${change.toFixed(2)}%`;
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

// 转换 API 返回的 K线数据为图表格式
const transformKlineData = (data: KlineData[]): ChartKLineData => {
  const dates: string[] = [];
  const values: number[][] = [];
  const volumes: number[] = [];

  data.forEach((item) => {
    dates.push(item.tradeDate);
    // ECharts candlestick: [Open, Close, Low, High]
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

// --- 数据获取 ---
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

// --- 事件处理 ---
const showDetail = (record: WatchlistStock) => {
  currentStock.value = record;
  detailVisible.value = true;
  chartPeriod.value = "daily";
  fetchHistory(record.id, "daily");
};

const handlePeriodChange = (period: string | number) => {
  if (currentStock.value) {
    fetchHistory(currentStock.value.id, period as KlinePeriod);
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
    handleRefresh(true);
  } catch (error) {
    Message.error("删除失败");
  }
};

// 获取股票列表
const fethcStockOption = async () => {
  const result: any = await marketApi.getOptions();
  allStockOptions.value = result.data;
};

// 防抖搜索
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

// =====================================================================
//                       5. 生命周期与监听
// =====================================================================
let refreshTimer: number | null = null;

onMounted(() => {
  handleRefresh();
  fethcStockOption();

  // 每5分钟自动刷新
  refreshTimer = window.setInterval(() => {
    handleRefresh(true);
  }, 5 * 60 * 1000);
});

onUnmounted(() => {
  // 组件卸载时清除定时器
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>
