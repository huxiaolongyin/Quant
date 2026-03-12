<template>
  <div class="min-h-screen flex flex-col">
    <div class="page-header-with-subtitle">
      <p class="page-subtitle mt-1">选择一个内置策略模板，快速开始您的量化交易</p>
      <a-button @click="handleBack">
        <template #icon
          ><span class="material-symbols-outlined text-base">arrow_back</span></template
        >
        返回列表
      </a-button>
    </div>

    <div class="flex items-center gap-4 mb-8">
      <span class="text-slate-600 dark:text-slate-300">分类筛选:</span>
      <a-radio-group
        v-model="categoryFilter"
        type="button"
        @change="handleCategoryChange"
      >
        <a-radio value="all" class="w-24">全部</a-radio>
        <a-radio v-for="cat in categories" :key="cat.value" :value="cat.value">
          {{ cat.label }}
        </a-radio>
      </a-radio-group>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <a-card
        hoverable
        class="card-hover cursor-pointer group border-2 border-dashed border-primary/30 hover:border-primary/60"
        @click="handleCustomCreate"
      >
        <template #title>
          <div class="flex items-center gap-2 text-primary">
            <span class="material-symbols-outlined">code</span>
            <span class="text-slate-900 dark:text-white">自定义代码</span>
          </div>
        </template>

        <div class="h-16 text-slate-500 dark:text-slate-400 text-sm line-clamp-3 mb-4">
          从头开始编写您的策略代码，完全自由定制交易逻辑。
        </div>

        <div class="mb-4">
          <span class="text-xs text-slate-400 block mb-2">适合</span>
          <div class="flex flex-wrap gap-1">
            <a-tag size="small" class="!bg-primary/10 !text-primary">高级用户</a-tag>
            <a-tag size="small" class="!bg-primary/10 !text-primary">自定义策略</a-tag>
          </div>
        </div>

        <div
          class="absolute bottom-0 left-0 w-full bg-primary/5 dark:bg-primary/10 border-t border-primary/20 p-2 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-b-lg"
        >
          <a-button type="primary" size="small">
            <template #icon
              ><span class="material-symbols-outlined text-base">edit</span></template
            >
            开始编写
          </a-button>
        </div>
      </a-card>

      <template v-if="!loading && filteredTemplates.length === 0">
        <div class="col-span-3 flex flex-col items-center justify-center py-12">
          <span class="material-symbols-outlined text-6xl text-slate-300 mb-4"
            >folder_off</span
          >
          <p class="text-slate-400">暂无策略模板</p>
        </div>
      </template>

      <a-card
        v-for="template in filteredTemplates"
        :key="template.id"
        hoverable
        class="card-hover cursor-pointer group"
        @click="handleSelect(template)"
      >
        <template #title>
          <div class="flex items-center justify-between">
            <span
              class="truncate pr-2 text-slate-900 dark:text-white"
              :title="template.name"
            >
              {{ template.name }}
            </span>
            <a-tag v-if="template.is_builtin" color="blue" size="small" bordered
              >内置</a-tag
            >
          </div>
        </template>

        <div class="h-16 text-slate-500 dark:text-slate-400 text-sm line-clamp-3 mb-4">
          {{ template.description }}
        </div>

        <div class="mb-4">
          <span class="text-xs text-slate-400 block mb-2">策略分类</span>
          <a-tag :color="getCategoryColor(template.category)" size="small">
            {{ getCategoryLabel(template.category) }}
          </a-tag>
        </div>

        <div v-if="template.params && template.params.length > 0" class="mb-4">
          <span class="text-xs text-slate-400 block mb-2">可配置参数</span>
          <div class="flex flex-wrap gap-1">
            <a-tag
              v-for="param in template.params.slice(0, 4)"
              :key="param.name"
              size="small"
              class="!bg-slate-100 dark:!bg-slate-900"
            >
              {{ param.display_name }}
            </a-tag>
            <a-tag
              v-if="template.params.length > 4"
              size="small"
              class="!bg-slate-100 dark:!bg-slate-900"
            >
              +{{ template.params.length - 4 }}
            </a-tag>
          </div>
        </div>

        <div class="flex flex-wrap gap-1">
          <a-tag
            v-for="tag in template.tags"
            :key="tag"
            size="small"
            class="!bg-primary/10 !text-primary"
          >
            {{ tag }}
          </a-tag>
        </div>

        <div
          class="absolute bottom-0 left-0 w-full bg-primary/5 dark:bg-primary/10 border-t border-primary/20 p-2 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-b-lg"
        >
          <a-button type="primary" size="small">
            <template #icon
              ><span class="material-symbols-outlined text-base">add</span></template
            >
            使用此模板
          </a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { strategyApi } from '@/api/strategy'
import { STRATEGY_CATEGORY_MAP, type StrategyTemplate } from '@/types/strategy'
import { Message } from '@arco-design/web-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const templates = ref<StrategyTemplate[]>([])
const categoryFilter = ref('all')

const categories = computed(() => {
  const cats = Object.entries(STRATEGY_CATEGORY_MAP).map(([value, label]) => ({ value, label }))
  return cats
})

const filteredTemplates = computed(() => {
  if (categoryFilter.value === 'all') return templates.value
  return templates.value.filter(t => t.category === categoryFilter.value)
})

const getCategoryLabel = (category: string) => STRATEGY_CATEGORY_MAP[category] || category

const getCategoryColor = (category: string): string => {
  const colorMap: Record<string, string> = {
    trend: 'green',
    mean_reversion: 'blue',
    momentum: 'orange',
    volume: 'purple',
    arbitrage: 'cyan'
  }
  return colorMap[category] || 'gray'
}

const loadTemplates = async () => {
  loading.value = true
  try {
    const res = await strategyApi.getTemplates()
    templates.value = res.data || []
  } catch {
    Message.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

const handleCategoryChange = () => {
}

const handleSelect = (template: StrategyTemplate) => {
  router.push({
    name: 'StrategyCreateFromTemplate',
    params: { templateId: template.id }
  })
}

const handleBack = () => {
  router.push({ name: 'StrategyList' })
}

const handleCustomCreate = () => {
  router.push({ name: 'StrategyEditor' })
}

onMounted(() => {
  loadTemplates()
})
</script>
