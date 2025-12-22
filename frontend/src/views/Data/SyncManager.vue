<template>
  <div class="py-2 px-6 space-y-6">
    <!-- 顶部标题与操作区 -->
    <div class="flex justify-between items-center">
      <div class="text-gray-500 text-sm">管理行情数据的下载、清洗与入库任务</div>
      <div class="space-x-3">
        <!-- 自动调度配置 -->
        <a-popover trigger="click" position="br">
          <a-button :loading="isLoading" class="rounded-lg">
            <template #icon><icon-settings /></template>
            定时调度设置
          </a-button>
          <template #content>
            <div class="p-2 w-64">
              <div class="flex justify-between items-center mb-3">
                <span class="text-gray-700 font-medium">每日自动同步</span>
                <a-switch v-model="scheduler.enabled" size="small" />
              </div>
              <div v-if="scheduler.enabled" class="space-y-3">
                <div class="text-xs text-gray-500">触发时间 (收盘后)</div>
                <a-time-picker v-model="scheduler.time" format="HH:mm" class="w-full" />
              </div>
            </div>
          </template>
        </a-popover>

        <!-- 补数按钮 -->
        <a-button @click="openBackfillModal" class="rounded-lg" :disabled="isSyncing">
          <template #icon><icon-history /></template>
          历史补数
        </a-button>

        <!-- 立即同步按钮 -->
        <a-tooltip content="16:00前同步上一个股票日数据，16:00之后同步今天和上一个股票日数据" position="left">
          <a-button type="primary" status="success" class="rounded-lg" :loading="isSyncing" @click="handleDailySync">
            <template #icon><icon-sync /></template>
            {{ isSyncing ? "同步中..." : "立即同步" }}
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <!-- 状态概览卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <a-card :loading="isLoading" hoverable class="rounded-lg border-gray-100">
        <a-statistic title="数据覆盖范围" :value="summary.statDays" show-group-separator>
          <template #prefix><icon-calendar /></template>
          <template #suffix>天</template>
        </a-statistic>
        <div class="mt-2 text-xs text-gray-400">{{ summary.dataRange }}</div>
      </a-card>

      <a-card :loading="isLoading" hoverable class="rounded-lg border-gray-100">
        <a-statistic title="上次同步时间" :value="formattedlastSyncTime" val format="YYYY-MM-DD HH:mm:ss">
          <template #prefix><icon-schedule /></template>
        </a-statistic>
        <div class="mt-2 flex items-center text-xs">
          <span class="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
          <span class="text-green-600">状态正常</span>
        </div>
      </a-card>

      <a-card :loading="isLoading" hoverable class="rounded-lg border-gray-100">
        <a-statistic title="入库股票数量" :value="summary.stockCount" animation>
          <template #prefix><icon-bar-chart /></template>
        </a-statistic>
        <div class="mt-2 text-xs text-gray-400">包含 A 股主板</div>
      </a-card>
    </div>

    <!-- 任务进度条 (前端模拟轮询效果) -->
    <transition enter-active-class="animate-fade-in-down" leave-active-class="animate-fade-out-up">
      <a-card v-if="isSyncing" class="border-blue-100 bg-blue-50">
        <div class="flex justify-between items-center mb-2">
          <span class="font-medium text-blue-800 flex items-center">
            <icon-loading class="animate-spin mr-2" />
            正在执行: {{ currentTaskName }}
          </span>
          <span class="text-blue-600 font-mono">{{ syncProgress }}%</span>
        </div>
        <a-progress :percent="syncProgress / 100"
          :color="{ '0%': 'rgb(var(--primary-6))', '100%': 'rgb(var(--success-6))' }" size="large" animation />
        <div class="mt-2 text-xs text-gray-500 font-mono">Log: {{ currentLog }}</div>
      </a-card>
    </transition>

    <!-- 同步历史记录表格 -->
    <a-card title="同步历史记录" :bordered="false" class="shadow-sm rounded-lg">
      <a-table :data="historyLogs" :loading="isTableLoading" :pagination="{
        total: pagination.total,
        current: pagination.page,
        pageSize: pagination.pageSize,
        showTotal: true,
      }" @page-change="onPageChange">
        <template #columns>
          <a-table-column title="任务ID" data-index="id" :width="100" />
          <a-table-column title="同步类型" data-index="type">
            <template #cell="{ record }">
              <a-tag :color="record.type === 'auto'
                ? 'blue'
                : record.type === 'manual'
                  ? 'green'
                  : 'orange'
                ">
                {{
                  record.type === "auto"
                    ? "自动调度"
                    : record.type === "manual"
                      ? "手动同步"
                      : "历史补数"
                }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="数据区间" data-index="range" />
          <a-table-column title="开始时间" data-index="startTime" />
          <a-table-column title="耗时" data-index="duration" />
          <a-table-column title="状态" data-index="status">
            <template #cell="{ record }">
              <span v-if="record.status === 'success'" class="flex items-center text-green-600">
                <icon-check-circle-fill class="mr-1" />
                成功
              </span>
              <span v-else-if="record.status === 'running'" class="flex items-center text-blue-600">
                <icon-sync class="mr-1 animate-spin" />
                运行中
              </span>
              <span v-else class="flex items-center text-red-600">
                <icon-close-circle-fill class="mr-1" />
                失败
              </span>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 补数模态框 -->
    <a-modal v-model:visible="backfillModalVisible" title="历史数据补录" @ok="handleConfirmBackfill">
      <div class="space-y-4">
        <a-alert>补录数据将在后台队列中执行，这可能需要几分钟时间。</a-alert>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            选择补录时间段
          </label>
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
import {
  IconBarChart,
  IconCalendar,
  IconCheckCircleFill,
  IconCloseCircleFill,
  IconHistory,
  IconLoading,
  IconSchedule,
  IconSettings,
  IconSync,
} from "@arco-design/web-vue/es/icon";
import dayjs from "dayjs";
import { computed, onMounted, reactive, ref } from "vue";

// --- 状态定义 ---
const isLoading = ref(false); // 全局/概览加载
const isTableLoading = ref(false); // 表格加载
const isSyncing = ref(false); // 任务运行状态

// 概览数据
const summary = reactive<Partial<SyncSummary>>({
  lastSyncTime: 0,
  dataRange: "-",
  statDays: 0,
  stockCount: 0,
});
const scheduler = reactive({ enabled: false, time: "00:00" });
const formattedlastSyncTime = computed(() => {
  return dayjs(summary.lastSyncTime).toDate();
});
// 日志列表
const historyLogs = ref<SyncLog[]>([]);
const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

// UI 交互状态
const backfillModalVisible = ref(false);
const backfillRange = ref([]);
const syncProgress = ref(0);
const currentTaskName = ref("");
const currentLog = ref("");

// --- 初始化 ---
onMounted(() => {
  loadDashboard();
});
// 1. 加载页面数据
const loadDashboard = async () => {
  isLoading.value = true;
  try {
    // 获取概览
    const res = (await syncApi.summary()).data;
    summary.lastSyncTime = res.lastSyncTime;
    summary.dataRange = res.dataRange;
    summary.statDays = res.statDays;
    summary.stockCount = res.stockCount;
    Object.assign(scheduler, res.scheduler);

    // 获取第一页日志
    await fetchLogs(1);
  } catch (error) {
    Message.error("无法连接到数据服务");
  } finally {
    isLoading.value = false;
  }
};

// 2. 获取日志 (支持分页)
const fetchLogs = async (page: number) => {
  isTableLoading.value = true;
  try {
    const res = (await syncApi.logs({ page: page, pageSize: pagination.pageSize })).data;
    historyLogs.value = res.list;
    pagination.page = res.page;
    pagination.total = res.total;
  } catch (error) {
    Message.error("加载日志失败");
  } finally {
    isTableLoading.value = false;
  }
};

const onPageChange = (page: number) => {
  fetchLogs(page);
};

// 3. 触发日级同步
const handleDailySync = async () => {
  if (isSyncing.value) return;

  try {
    // 调用后端
    await syncApi.trigger({ type: "manual", dataRange: backfillRange.value });

    // 成功后，前端开始显示进度效果
    startFakeProgress("手动同步 (T+1)");
  } catch (error: any) {
    Message.error(error.message || "同步触发失败");
  }
};

// 4. 触发补数
const handleConfirmBackfill = async () => {
  if (!backfillRange.value || backfillRange.value.length !== 2) {
    Message.warning("请选择完整的时间段");
    return false;
  }

  try {
    await syncApi.trigger({ type: "backfill", dataRange: backfillRange.value });
    backfillModalVisible.value = false;
    startFakeProgress("历史补数任务");
    return true;
  } catch (error: any) {
    Message.error("补数任务提交失败");
    return false;
  }
};

const openBackfillModal = () => (backfillModalVisible.value = true);

// --- 模拟进度轮询 (视觉效果) ---
// 在真实场景中，你会使用 setInterval 定期调用 getSummary() 检查后端 task.progress
const startFakeProgress = (taskName: string) => {
  isSyncing.value = true;
  currentTaskName.value = taskName;
  syncProgress.value = 0;
  currentLog.value = "初始化任务队列...";

  const timer = setInterval(() => {
    syncProgress.value += Math.floor(Math.random() * 5) + 2;

    // 模拟变化的日志
    if (syncProgress.value < 30) currentLog.value = "正在下载行情数据...";
    else if (syncProgress.value < 70) currentLog.value = "正在清洗并写入数据库...";
    else currentLog.value = "正在更新因子缓存...";

    if (syncProgress.value >= 100) {
      clearInterval(timer);
      isSyncing.value = false;
      Message.success("任务执行完成");
      fetchLogs(1); // 刷新日志列表
    }
  }, 200);
};
</script>
