<template>
  <div class="py-2 px-6 space-y-6">
    <div class="page-header-with-subtitle">
      <div class="text-muted text-sm">管理行情数据的下载、清洗与入库任务</div>
      <div class="space-x-3">
        <a-popover trigger="click" position="br">
          <a-button :loading="isLoading" class="rounded-lg">
            <template #icon><span class="material-symbols-outlined text-base">settings</span></template>
            定时调度设置
          </a-button>
          <template #content>
            <div class="p-2 w-64">
              <div class="flex justify-between items-center mb-3">
                <span class="text-slate-700 dark:text-slate-300 font-medium">每日自动同步</span>
                <a-switch v-model="scheduler.enabled" size="small" />
              </div>
              <div v-if="scheduler.enabled" class="space-y-3">
                <div class="text-xs text-slate-500">触发时间 (收盘后)</div>
                <a-time-picker v-model="scheduler.time" format="HH:mm" class="w-full" />
              </div>
            </div>
          </template>
        </a-popover>

        <a-button @click="openBackfillModal" class="rounded-lg" :disabled="isSyncing">
          <template #icon><span class="material-symbols-outlined text-base">history</span></template>
          历史补数
        </a-button>

        <a-tooltip content="16:00前同步上一个股票日数据，16:00之后同步今天和上一个股票日数据" position="left">
          <a-button type="primary" status="success" class="rounded-lg" :loading="isSyncing" @click="handleDailySync">
            <template #icon><span class="material-symbols-outlined text-base">sync</span></template>
            {{ isSyncing ? "同步中..." : "立即同步" }}
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <a-card :loading="isLoading" hoverable class="stat-card-sm">
        <a-statistic title="数据覆盖范围" :value="summary.statDays" show-group-separator>
          <template #prefix><span class="material-symbols-outlined text-base">calendar_month</span></template>
          <template #suffix>天</template>
        </a-statistic>
        <div class="mt-2 text-xs text-muted">{{ summary.dataRange }}</div>
      </a-card>

      <a-card :loading="isLoading" hoverable class="stat-card-sm">
        <a-statistic title="上次同步时间" :value="formattedlastSyncTime" val format="YYYY-MM-DD HH:mm:ss">
          <template #prefix><span class="material-symbols-outlined text-base">schedule</span></template>
        </a-statistic>
        <div class="mt-2 flex items-center text-xs">
          <span class="w-2 h-2 rounded-full bg-success mr-2"></span>
          <span class="text-success">状态正常</span>
        </div>
      </a-card>

      <a-card :loading="isLoading" hoverable class="stat-card-sm">
        <a-statistic title="入库股票数量" :value="summary.stockCount" animation>
          <template #prefix><span class="material-symbols-outlined text-base">bar_chart</span></template>
        </a-statistic>
        <div class="mt-2 text-xs text-muted">包含 A 股主板</div>
      </a-card>
    </div>

    <transition enter-active-class="animate-fade-in-down" leave-active-class="animate-fade-out-up">
      <a-card v-if="isSyncing" class="border-primary/20 bg-primary/5 dark:bg-primary/10">
        <div class="flex justify-between items-center mb-2">
          <span class="font-medium text-primary flex items-center">
            <span class="material-symbols-outlined text-base animate-spin mr-2">sync</span>
            正在执行: {{ currentTaskName }}
          </span>
          <span class="text-primary font-mono">{{ syncProgress }}%</span>
        </div>
        <a-progress :percent="syncProgress / 100" :color="{ '0%': '#137fec', '100%': '#22c55e' }" size="large" animation />
        <div class="mt-2 text-xs text-slate-500 font-mono">Log: {{ currentLog }}</div>
      </a-card>
    </transition>

    <a-card title="同步历史记录" :bordered="false" class="card-shadow rounded-lg">
      <a-table :data="historyLogs" :loading="isTableLoading" :pagination="{ total: pagination.total, current: pagination.page, pageSize: pagination.pageSize, showTotal: true }" @page-change="onPageChange">
        <template #columns>
          <a-table-column title="任务ID" data-index="id" :width="100" />
          <a-table-column title="同步类型" data-index="type">
            <template #cell="{ record }">
              <a-tag :color="record.type === 'auto' ? 'blue' : record.type === 'manual' ? 'green' : 'orange'">
                {{ record.type === "auto" ? "自动调度" : record.type === "manual" ? "手动同步" : "历史补数" }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="数据区间" data-index="range" />
          <a-table-column title="开始时间" data-index="startTime" />
          <a-table-column title="耗时" data-index="duration" />
          <a-table-column title="状态" data-index="status">
            <template #cell="{ record }">
              <span v-if="record.status === 'success'" class="flex items-center text-success">
                <span class="material-symbols-outlined text-base mr-1">check_circle</span>
                成功
              </span>
              <span v-else-if="record.status === 'running'" class="flex items-center text-primary">
                <span class="material-symbols-outlined text-base mr-1 animate-spin">sync</span>
                运行中
              </span>
              <span v-else class="flex items-center text-danger">
                <span class="material-symbols-outlined text-base mr-1">cancel</span>
                失败
              </span>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:visible="backfillModalVisible" title="历史数据补录" @ok="handleConfirmBackfill">
      <div class="space-y-4">
        <a-alert>补录数据将在后台队列中执行，这可能需要几分钟时间。</a-alert>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">选择补录时间段</label>
          <a-range-picker v-model="backfillRange" style="width: 100%" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { syncApi } from "@/api/sync";
import type { SyncLog, SyncSummary } from "@/types/api";
import { Message } from "@arco-design/web-vue";
import dayjs from "dayjs";
import { computed, onMounted, reactive, ref } from "vue";

const isLoading = ref(false);
const isTableLoading = ref(false);
const isSyncing = ref(false);

const summary = reactive<Partial<SyncSummary>>({ lastSyncTime: 0, dataRange: "-", statDays: 0, stockCount: 0 });
const scheduler = reactive({ enabled: false, time: "00:00" });
const formattedlastSyncTime = computed(() => dayjs(summary.lastSyncTime).toDate());
const historyLogs = ref<SyncLog[]>([]);
const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

const backfillModalVisible = ref(false);
const backfillRange = ref([]);
const syncProgress = ref(0);
const currentTaskName = ref("");
const currentLog = ref("");

onMounted(() => { loadDashboard(); });

const loadDashboard = async () => {
  isLoading.value = true;
  try {
    const res = (await syncApi.summary()).data;
    summary.lastSyncTime = res.lastSyncTime;
    summary.dataRange = res.dataRange;
    summary.statDays = res.statDays;
    summary.stockCount = res.stockCount;
    Object.assign(scheduler, res.scheduler);
    await fetchLogs(1);
  } catch (error) { Message.error("无法连接到数据服务"); }
  finally { isLoading.value = false; }
};

const fetchLogs = async (page: number) => {
  isTableLoading.value = true;
  try {
    const res = (await syncApi.logs({ page: page, pageSize: pagination.pageSize })).data;
    historyLogs.value = res.list;
    pagination.page = res.page;
    pagination.total = res.total;
  } catch (error) { Message.error("加载日志失败"); }
  finally { isTableLoading.value = false; }
};

const onPageChange = (page: number) => { fetchLogs(page); };

const handleDailySync = async () => {
  if (isSyncing.value) return;
  try {
    await syncApi.trigger({ type: "manual", dataRange: backfillRange.value });
    startFakeProgress("手动同步 (T+1)");
  } catch (error: any) { Message.error(error.message || "同步触发失败"); }
};

const handleConfirmBackfill = async () => {
  if (!backfillRange.value || backfillRange.value.length !== 2) { Message.warning("请选择完整的时间段"); return false; }
  try {
    await syncApi.trigger({ type: "backfill", dataRange: backfillRange.value });
    backfillModalVisible.value = false;
    startFakeProgress("历史补数任务");
    return true;
  } catch (error: any) { Message.error("补数任务提交失败"); return false; }
};

const openBackfillModal = () => (backfillModalVisible.value = true);

const startFakeProgress = (taskName: string) => {
  isSyncing.value = true;
  currentTaskName.value = taskName;
  syncProgress.value = 0;
  currentLog.value = "初始化任务队列...";

  const timer = setInterval(() => {
    syncProgress.value += Math.floor(Math.random() * 5) + 2;
    if (syncProgress.value < 30) currentLog.value = "正在下载行情数据...";
    else if (syncProgress.value < 70) currentLog.value = "正在清洗并写入数据库...";
    else currentLog.value = "正在更新因子缓存...";

    if (syncProgress.value >= 100) {
      clearInterval(timer);
      isSyncing.value = false;
      Message.success("任务执行完成");
      fetchLogs(1);
    }
  }, 200);
};
</script>