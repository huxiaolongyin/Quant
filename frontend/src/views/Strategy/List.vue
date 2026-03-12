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
      <a-input-search
        v-model="search"
        placeholder="搜索策略名称..."
        class="w-64"
        allow-clear
        @search="handleSearch"
        @clear="handleSearch"
        @press-enter="handleSearch"
      />
      <a-radio-group v-model="statusFilter" type="button" @change="handleStatusChange">
        <a-radio value="all" class="w-24">全部</a-radio>
        <a-radio value="draft">草稿</a-radio>
        <a-radio value="running">运行中</a-radio>
        <a-radio value="stopped">已停止</a-radio>
        <a-radio value="error">错误</a-radio>
      </a-radio-group>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <a-spin dot />
    </div>

    <div
      v-else-if="list.length === 0"
      class="flex flex-col items-center justify-center py-20"
    >
      <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">code_off</span>
      <p class="text-slate-400">暂无策略数据</p>
      <a-button type="primary" class="mt-4" @click="handleCreate">
        <template #icon
          ><span class="material-symbols-outlined text-base">add</span></template
        >
        新建第一个策略
      </a-button>
    </div>

    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
    >
      <a-card
        v-for="item in list"
        :key="item.id"
        hoverable
        class="card-hover cursor-pointer group relative"
        @click="handleEdit(item.id)"
      >
        <template #title>
          <div class="flex items-center justify-between">
            <span
              class="truncate pr-2 text-slate-900 dark:text-white"
              :title="item.name"
              >{{ item.name }}</span
            >
            <a-tag :color="getStatusColor(item.status)" size="small" bordered>
              {{ getStatusLabel(item.status) }}
            </a-tag>
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
              <a-doption @click.stop="handleCopy(item)">
                <span class="material-symbols-outlined text-base mr-1">content_copy</span>
                复制策略
              </a-doption>
              <a-doption @click.stop="handleExport(item)">
                <span class="material-symbols-outlined text-base mr-1">download</span>
                导出代码
              </a-doption>
              <a-doption class="!text-danger" @click.stop="handleDelete(item.id)">
                <span class="material-symbols-outlined text-base mr-1">delete</span>
                删除
              </a-doption>
            </template>
          </a-dropdown>
        </template>

        <div class="h-10 text-slate-500 dark:text-slate-400 text-xs line-clamp-2 mb-4">
          {{ item.description || "暂无描述" }}
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
              {{ ((item.returns ?? 0) > 0 ? "+" : "") + (item.returns ?? 0).toFixed(2) }}%
            </div>
          </div>
          <div class="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
          <div class="text-center">
            <div class="text-xs text-slate-400 mb-1">胜率</div>
            <div class="font-bold text-lg text-slate-700 dark:text-slate-200">
              {{ (item.win_rate ?? 0).toFixed(1) }}%
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center mt-2">
          <div class="flex gap-1 flex-wrap">
            <a-tag
              v-for="tag in item.tags"
              :key="tag"
              size="small"
              class="!bg-slate-100 dark:!bg-slate-900 !text-slate-500 dark:!text-slate-400"
              >{{ tag }}</a-tag
            >
          </div>
          <span class="text-xs text-slate-400">{{ formatDate(item.updated_at) }}</span>
        </div>

        <div
          class="absolute bottom-0 left-0 w-full bg-primary/5 dark:bg-primary/10 border-t border-primary/20 p-2 flex justify-around opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-b-lg"
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

    <div v-if="pagination.total > pagination.pageSize" class="flex justify-center mt-8">
      <a-pagination
        v-model:current="pagination.page"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        show-total
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { strategyApi } from '@/api/strategy'
import { STRATEGY_STATUS_MAP, type StrategyListItem, type StrategyStatus } from '@/types/strategy'
import { Message, Modal } from '@arco-design/web-vue'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const list = ref<StrategyListItem[]>([])
const search = ref('')
const statusFilter = ref<string>('all')

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
})

const getStatusLabel = (status: StrategyStatus) => STRATEGY_STATUS_MAP[status]?.label || status
const getStatusColor = (status: StrategyStatus) => STRATEGY_STATUS_MAP[status]?.color || 'gray'

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split(' ')[0] || dateStr.split('T')[0]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await strategyApi.getList({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: search.value || undefined,
      status: statusFilter.value !== 'all' ? statusFilter.value as StrategyStatus : undefined
    })
    list.value = res.data.list
    pagination.total = res.data.total
  } catch (err) {
    Message.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleStatusChange = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadData()
}

const handleEdit = (id: string) => {
  router.push({ name: 'StrategyEditor', params: { id } })
}

const handleCreate = () => {
  router.push({ name: 'StrategyTemplates' })
}

const handleRun = (id: string) => {
  router.push({ name: 'BacktestReport', query: { strategyId: id } })
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    content: '删除后无法恢复，确定要删除这个策略吗？',
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await strategyApi.delete(id)
        Message.success('删除成功')
        loadData()
      } catch (err) {
        Message.error('删除失败')
      }
    }
  })
}

const handleCopy = (item: StrategyListItem) => {
  router.push({
    name: 'StrategyEditor',
    query: { copyFrom: item.id, name: `${item.name}_副本` }
  })
}

const handleExport = (item: StrategyListItem) => {
  strategyApi.getDetail(item.id).then(res => {
    const blob = new Blob([res.data.code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.name}.py`
    a.click()
    URL.revokeObjectURL(url)
    Message.success('导出成功')
  }).catch(() => {
    Message.error('导出失败')
  })
}

onMounted(() => {
  loadData()
})
</script>
