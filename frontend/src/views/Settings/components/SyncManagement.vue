<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <div class="text-muted text-sm">配置数据同步调度策略，管理行情数据的下载与入库</div>
    </div>

    <a-card title="定时调度设置" :bordered="false" class="card-shadow">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <div>
            <div class="font-medium">每日自动同步</div>
            <div class="text-xs text-slate-500 mt-1">在指定时间自动执行行情数据同步</div>
          </div>
          <a-switch
            v-model="scheduler.enabled"
            size="small"
            @change="handleSchedulerToggle"
          />
        </div>
        <div
          v-if="scheduler.enabled"
          class="flex items-center gap-4 pt-2 border-t border-slate-100 dark:border-slate-800"
        >
          <span class="text-sm text-slate-600 dark:text-slate-400"
            >触发时间 (收盘后)</span
          >
          <a-time-picker
            v-model="scheduler.time"
            format="HH:mm"
            class="w-32"
            @change="handleTimeChange"
          />
        </div>
      </div>
    </a-card>

    <a-card title="手动操作" :bordered="false" class="card-shadow">
      <div class="flex items-center gap-4">
        <a-tooltip
          content="16:00前同步上一个股票日数据，16:00之后同步今天和上一个股票日数据"
          position="top"
        >
          <a-button
            type="primary"
            status="success"
            :loading="isSyncing"
            @click="handleDailySync"
          >
            <template #icon
              ><span class="material-symbols-outlined text-base">sync</span></template
            >
            {{ isSyncing ? "同步中..." : "立即同步" }}
          </a-button>
        </a-tooltip>

        <a-button :disabled="isSyncing" @click="openBackfillModal">
          <template #icon
            ><span class="material-symbols-outlined text-base">history</span></template
          >
          历史补数
        </a-button>
      </div>

      <transition
        enter-active-class="animate-fade-in-down"
        leave-active-class="animate-fade-out-up"
      >
        <div
          v-if="isSyncing"
          class="mt-4 p-4 rounded-lg border border-primary/20 bg-primary/5 dark:bg-primary/10"
        >
          <div class="flex justify-between items-center mb-2">
            <span class="font-medium text-primary flex items-center">
              <span class="material-symbols-outlined text-base animate-spin mr-2"
                >sync</span
              >
              正在执行: {{ currentTaskName }}
            </span>
            <span class="text-primary font-mono">{{ syncProgress }}%</span>
          </div>
          <a-progress
            :percent="syncProgress / 100"
            :color="{ '0%': '#137fec', '100%': '#22c55e' }"
            size="large"
            animation
          />
          <div class="mt-2 text-xs text-slate-500 font-mono">Log: {{ currentLog }}</div>
        </div>
      </transition>
    </a-card>

    <a-card title="同步历史记录" :bordered="false" class="card-shadow">
      <a-table
        :data="historyLogs"
        :loading="isTableLoading"
        :pagination="{
          total: pagination.total,
          current: pagination.page,
          pageSize: pagination.pageSize,
          showTotal: true,
        }"
        @page-change="onPageChange"
      >
        <template #columns>
          <a-table-column title="任务ID" data-index="id" :width="100" />
          <a-table-column title="同步类型" data-index="type">
            <template #cell="{ record }">
              <a-tag
                :color="
                  record.type === 'auto'
                    ? 'blue'
                    : record.type === 'manual'
                    ? 'green'
                    : 'orange'
                "
              >
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
              <span
                v-if="record.status === 'success'"
                class="flex items-center text-success"
              >
                <span class="material-symbols-outlined text-base mr-1">check_circle</span>
                成功
              </span>
              <span
                v-else-if="record.status === 'running'"
                class="flex items-center text-primary"
              >
                <span class="material-symbols-outlined text-base mr-1 animate-spin"
                  >sync</span
                >
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

    <a-modal
      v-model:visible="backfillModalVisible"
      title="历史数据补录"
      @ok="handleConfirmBackfill"
    >
      <div class="space-y-4">
        <a-alert>补录数据将在后台队列中执行，这可能需要几分钟时间。</a-alert>
        <div>
          <label
            class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
          >
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
import type { SyncLog } from "@/types/api";
import { Message } from "@arco-design/web-vue";
import { onMounted, reactive, ref } from "vue";

const isTableLoading = ref(false);
const isSyncing = ref(false);

const scheduler = reactive({ enabled: false, time: "17:30" });
const historyLogs = ref<SyncLog[]>([]);
const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

const backfillModalVisible = ref(false);
const backfillRange = ref<string[]>([]);
const syncProgress = ref(0);
const currentTaskName = ref("");
const currentLog = ref("");

onMounted(() => {
  loadSchedulerConfig();
  fetchLogs(1);
});

const loadSchedulerConfig = async () => {
  try {
    const res = (await syncApi.summary()).data;
    scheduler.enabled = res.scheduler?.enabled ?? false;
    scheduler.time = res.scheduler?.time ?? "17:30";
  } catch {
    Message.error("无法加载调度配置");
  }
};

const handleSchedulerToggle = async (value: boolean | number | string) => {
  try {
    await syncApi.updateScheduler({
      enabled: value as boolean,
      time: scheduler.time,
    });
    Message.success(value ? "已启用自动同步" : "已禁用自动同步");
  } catch {
    Message.error("配置保存失败");
    scheduler.enabled = !value;
  }
};

const handleTimeChange = async () => {
  try {
    await syncApi.updateScheduler({
      enabled: scheduler.enabled,
      time: scheduler.time,
    });
    Message.success("触发时间已更新");
  } catch {
    Message.error("配置保存失败");
  }
};

const fetchLogs = async (page: number) => {
  isTableLoading.value = true;
  try {
    const res = (await syncApi.logs({ page, pageSize: pagination.pageSize })).data;
    historyLogs.value = res.list;
    pagination.page = res.page;
    pagination.total = res.total;
  } catch {
    Message.error("加载日志失败");
  } finally {
    isTableLoading.value = false;
  }
};

const onPageChange = (page: number) => {
  fetchLogs(page);
};

const handleDailySync = async () => {
  if (isSyncing.value) return;
  try {
    await syncApi.trigger({ type: "manual", dataRange: [] });
    startFakeProgress("手动同步 (T+1)");
  } catch (error: any) {
    Message.error(error.message || "同步触发失败");
  }
};

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
  } catch {
    Message.error("补数任务提交失败");
    return false;
  }
};

const openBackfillModal = () => {
  backfillModalVisible.value = true;
};

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
