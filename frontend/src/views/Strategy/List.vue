<template>
  <div class="p-6 bg-gray-50 min-h-screen flex flex-col">
    <!-- 顶部操作栏 -->
    <div class="flex justify-between items-center mb-6">
      <p class="text-gray-500 text-sm mt-1">管理和运行您的量化交易策略</p>
      <a-button type="primary" size="large" class="rounded-lg" @click="handleCreate">
        <template #icon><icon-plus /></template>
        新建策略
      </a-button>
    </div>

    <!-- 筛选/搜索栏 (可选) -->
    <div class="bg-white p-4 rounded-lg shadow-sm mb-6 flex gap-4 items-center">
      <a-input-search placeholder="搜索策略名称..." class="w-64" />
      <a-radio-group type="button" default-value="all">
        <a-radio value="all">全部</a-radio>
        <a-radio value="running">运行中</a-radio>
        <a-radio value="backtest">回测中</a-radio>
      </a-radio-group>
    </div>

    <!-- 策略列表 Grid -->
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
        class="transition-all duration-300 hover:-translate-y-1 cursor-pointer group"
        @click="handleEdit(item.id)"
      >
        <!-- 卡片头部 -->
        <template #title>
          <div class="flex items-center justify-between">
            <span class="truncate pr-2" :title="item.name">{{ item.name }}</span>
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
              class="!text-gray-400 hover:!text-gray-600"
              @click.stop
            >
              <template #icon><icon-more /></template>
            </a-button>
            <template #content>
              <a-doption><icon-copy /> 复制策略</a-doption>
              <a-doption><icon-download /> 导出代码</a-doption>
              <a-doption class="!text-red-500"><icon-delete /> 删除</a-doption>
            </template>
          </a-dropdown>
        </template>

        <!-- 卡片内容 -->
        <div class="h-10 text-gray-500 text-xs line-clamp-2 mb-4">
          {{ item.description }}
        </div>

        <!-- 绩效指标 -->
        <div class="flex justify-between items-center bg-gray-50 rounded p-3 mb-4">
          <div class="text-center">
            <div class="text-xs text-gray-400 mb-1">累计收益</div>
            <div
              class="font-bold text-lg"
              :class="item.returns >= 0 ? 'text-red-500' : 'text-green-500'"
            >
              {{ item.returns > 0 ? "+" : "" }}{{ item.returns }}%
            </div>
          </div>
          <div class="w-px h-8 bg-gray-200"></div>
          <div class="text-center">
            <div class="text-xs text-gray-400 mb-1">胜率</div>
            <div class="font-bold text-lg text-gray-700">{{ item.winRate }}%</div>
          </div>
        </div>

        <!-- 底部标签和时间 -->
        <div class="flex justify-between items-center mt-2">
          <div class="flex gap-1">
            <a-tag
              v-for="tag in item.tags"
              :key="tag"
              size="small"
              class="!bg-gray-100 !text-gray-500"
              >{{ tag }}</a-tag
            >
          </div>
          <span class="text-xs text-gray-300">{{ item.updatedAt.split(" ")[0] }}</span>
        </div>

        <!-- 悬浮时显示的操作栏 (可选效果，如果不喜欢可以去掉 group-hover 类) -->
        <div
          class="absolute bottom-0 left-0 w-full bg-blue-50 border-t border-blue-100 p-2 flex justify-around opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <a-button type="text" size="small" @click.stop="handleRun(item.id)">
            <template #icon><icon-play-arrow /></template> 回测
          </a-button>
          <a-button type="text" size="small" @click.stop="handleEdit(item.id)">
            <template #icon><icon-edit /></template> 编辑
          </a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchGetStrategyList, type StrategyItem } from '@/api/strategy';
import { Message } from '@arco-design/web-vue';
import {
    IconCopy,
    IconDelete,
    IconDownload,
    IconEdit,
    IconMore,
    IconPlayArrow,
    IconPlus
} from '@arco-design/web-vue/es/icon';
import { onMounted, ref } from 'vue';
// 假设你有路由
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
  router.push({ name: 'StrategyEditor' }); // 无 ID，表示新建
};

const handleRun = (id: string) => {
  Message.success(`开始回测策略: ${id}`);
};

onMounted(() => {
  loadData();
});
</script>

<style scoped></style>
