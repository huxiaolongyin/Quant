<template>
  <div class="min-h-screen flex flex-col">
    <div class="page-header-with-subtitle">
      <p class="page-subtitle mt-1">管理和运行您的量化交易策略</p>
      <a-button type="primary" size="large" class="rounded-lg" @click="handleCreate">
        <template #icon
          ><span class="material-symbols-outlined text-base">add</span></template
        >
        新建策略
      </a-button>
    </div>

    <div class="flex items-center gap-4 mb-8">
      <a-input-search placeholder="搜索策略名称..." class="w-64" />
      <a-radio-group type="button" default-value="all">
        <a-radio value="all" class="w-24">全部</a-radio>
        <a-radio value="running">运行中</a-radio>
        <a-radio value="backtest">回测中</a-radio>
      </a-radio-group>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <a-spin dot />
    </div>

    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
    >
      <a-card
        v-for="item in list"
        :key="item.id"
        hoverable
        class="card-hover cursor-pointer group"
        @click="handleEdit(item.id)"
      >
        <template #title>
          <div class="flex items-center justify-between">
            <span
              class="truncate pr-2 text-slate-900 dark:text-white"
              :title="item.name"
              >{{ item.name }}</span
            >
            <a-tag v-if="item.status === 'running'" color="green" size="small" bordered
              >运行中</a-tag
            >
            <a-tag v-else color="gray" size="small" bordered>已停止</a-tag>
          </div>
        </template>

        <template #extra>
          <a-dropdown @select.stop>
            <a-button
              type="text"
              size="mini"
              class="!text-slate-400 hover:!text-slate-600"
              @click.stop
            >
              <template #icon
                ><span class="material-symbols-outlined text-base"
                  >more_vert</span
                ></template
              >
            </a-button>
            <template #content>
              <a-doption
                ><span class="material-symbols-outlined text-base mr-1"
                  >content_copy</span
                >
                复制策略</a-doption
              >
              <a-doption
                ><span class="material-symbols-outlined text-base mr-1">download</span>
                导出代码</a-doption
              >
              <a-doption class="!text-danger"
                ><span class="material-symbols-outlined text-base mr-1">delete</span>
                删除</a-doption
              >
            </template>
          </a-dropdown>
        </template>

        <div class="h-10 text-slate-500 dark:text-slate-400 text-xs line-clamp-2 mb-4">
          {{ item.description }}
        </div>

        <div
          class="flex justify-between items-center bg-slate-50 dark:bg-slate-950 rounded p-3 mb-4"
        >
          <div class="text-center">
            <div class="text-xs text-slate-400 mb-1">累计收益</div>
            <div
              class="font-bold text-lg"
              :class="item.returns >= 0 ? 'text-red-500' : 'text-green-500'"
            >
              {{ item.returns > 0 ? "+" : "" }}{{ item.returns }}%
            </div>
          </div>
          <div class="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
          <div class="text-center">
            <div class="text-xs text-slate-400 mb-1">胜率</div>
            <div class="font-bold text-lg text-slate-700 dark:text-slate-200">
              {{ item.winRate }}%
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center mt-2">
          <div class="flex gap-1">
            <a-tag
              v-for="tag in item.tags"
              :key="tag"
              size="small"
              class="!bg-slate-100 dark:!bg-slate-900 !text-slate-500 dark:!text-slate-400"
              >{{ tag }}</a-tag
            >
          </div>
          <span class="text-xs text-slate-400">{{ item.updatedAt.split(" ")[0] }}</span>
        </div>

        <div
          class="absolute bottom-0 left-0 w-full bg-primary/5 dark:bg-primary/10 border-t border-primary/20 p-2 flex justify-around opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <a-button type="text" size="small" @click.stop="handleRun(item.id)">
            <template #icon
              ><span class="material-symbols-outlined text-base"
                >play_arrow</span
              ></template
            >
            回测
          </a-button>
          <a-button type="text" size="small" @click.stop="handleEdit(item.id)">
            <template #icon
              ><span class="material-symbols-outlined text-base">edit</span></template
            >
            编辑
          </a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchGetStrategyList, type StrategyItem } from '@/api/strategy';
import { Message } from '@arco-design/web-vue';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const loading = ref(false);
const list = ref<StrategyItem[]>([]);

const loadData = async () => {
  loading.value = true;
  try {
    list.value = await fetchGetStrategyList();
  } catch (err) {
    Message.error('获取列表失败');
  } finally {
    loading.value = false;
  }
};

const handleEdit = (id: string) => {
  router.push({ name: 'StrategyEditor', params: { id } });
};

const handleCreate = () => {
  router.push({ name: 'StrategyEditor' });
};

const handleRun = (id: string) => {
  Message.success(`开始回测策略: ${id}`);
};

onMounted(() => {
  loadData();
});
</script>
