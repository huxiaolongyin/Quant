<template>
  <div class="min-h-screen flex flex-col">
    <div class="page-header-with-subtitle">
      <p class="page-subtitle mt-1" v-if="template">基于 {{ template.name }} 创建新策略</p>
      <a-button @click="handleBack">
        <template #icon><span class="material-symbols-outlined text-base">arrow_back</span></template>
        返回模板
      </a-button>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <a-spin dot />
    </div>

    <div v-else-if="!template" class="flex flex-col items-center justify-center py-20">
      <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">error</span>
      <p class="text-slate-400">模板不存在</p>
      <a-button type="primary" class="mt-4" @click="handleBack">返回模板列表</a-button>
    </div>

    <div v-else class="max-w-3xl mx-auto w-full px-4 py-8">
      <a-card class="mb-6">
        <template #title>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">description</span>
            模板信息
          </div>
        </template>
        <div class="space-y-3">
          <div>
            <span class="text-slate-500 text-sm">模板名称：</span>
            <span class="font-bold text-slate-800 dark:text-white">{{ template.name }}</span>
          </div>
          <div>
            <span class="text-slate-500 text-sm">模板描述：</span>
            <span class="text-slate-700 dark:text-slate-300">{{ template.description }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-500 text-sm">策略分类：</span>
            <a-tag :color="getCategoryColor(template.category)" size="small">
              {{ getCategoryLabel(template.category) }}
            </a-tag>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-500 text-sm">标签：</span>
            <a-tag
              v-for="tag in template.tags"
              :key="tag"
              size="small"
              class="!bg-primary/10 !text-primary"
            >
              {{ tag }}
            </a-tag>
          </div>
        </div>
      </a-card>

      <a-form :model="form" layout="vertical" @submit-success="handleSubmit">
        <a-card class="mb-6">
          <template #title>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">edit</span>
              基本信息
            </div>
          </template>

          <a-form-item field="name" label="策略名称" :rules="[{ required: true, message: '请输入策略名称' }]">
            <a-input v-model="form.name" placeholder="请输入策略名称" :max-length="200" show-word-limit />
          </a-form-item>

          <a-form-item field="description" label="策略描述">
            <a-textarea v-model="form.description" placeholder="请输入策略描述（可选）" :max-length="500" :auto-size="{ minRows: 2, maxRows: 4 }" />
          </a-form-item>
        </a-card>

        <a-card v-if="template.params && template.params.length > 0" class="mb-6">
          <template #title>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">tune</span>
              参数配置
            </div>
          </template>

          <div class="space-y-4">
            <div v-for="param in template.params" :key="param.name" class="flex items-start gap-4">
              <div class="w-32 shrink-0 pt-1">
                <label class="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {{ param.display_name }}
                </label>
                <p v-if="param.description" class="text-xs text-slate-400 mt-0.5">{{ param.description }}</p>
              </div>
              <div class="flex-1">
                <a-input-number
                  v-if="param.type === 'int'"
                  v-model="form.params[param.name]"
                  :placeholder="String(param.default)"
                  :min="param.min"
                  :max="param.max"
                  :precision="0"
                  class="w-full"
                />
                <a-input-number
                  v-else-if="param.type === 'float'"
                  v-model="form.params[param.name]"
                  :placeholder="String(param.default)"
                  :min="param.min"
                  :max="param.max"
                  class="w-full"
                />
                <a-input
                  v-else-if="param.type === 'str'"
                  v-model="form.params[param.name]"
                  :placeholder="String(param.default)"
                />
                <a-switch
                  v-else-if="param.type === 'bool'"
                  v-model="form.params[param.name]"
                />
              </div>
            </div>
          </div>
        </a-card>

        <a-card class="mb-6">
          <template #title>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">label</span>
              选择标签
            </div>
          </template>

          <div v-if="loadingTags" class="py-4">
            <a-spin size="small" />
          </div>
          <div v-else-if="tags.length === 0" class="text-slate-400 text-sm">
            暂无标签
          </div>
          <a-checkbox-group v-else v-model="form.tag_ids" direction="horizontal">
            <a-checkbox v-for="tag in tags" :key="tag.id" :value="tag.id">
              <a-tag :color="tag.color" size="small">{{ tag.name }}</a-tag>
            </a-checkbox>
          </a-checkbox-group>
        </a-card>

        <div class="flex justify-end gap-4">
          <a-button @click="handleBack">取消</a-button>
          <a-button type="primary" html-type="submit" :loading="submitting">
            <template #icon><span class="material-symbols-outlined text-base">add</span></template>
            创建策略
          </a-button>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { strategyApi } from '@/api/strategy'
import { STRATEGY_CATEGORY_MAP, type StrategyTemplateDetail, type StrategyParamDef, type StrategyTag } from '@/types/strategy'
import { Message } from '@arco-design/web-vue'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const loadingTags = ref(false)
const submitting = ref(false)
const template = ref<StrategyTemplateDetail | null>(null)
const tags = ref<StrategyTag[]>([])

const form = reactive({
  name: '',
  description: '',
  params: {} as Record<string, any>,
  tag_ids: [] as string[]
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

const loadTemplate = async () => {
  const templateId = route.params.templateId as string
  if (!templateId) {
    loading.value = false
    return
  }

  try {
    const res = await strategyApi.getTemplateDetail(templateId)
    template.value = res.data

    form.name = `${template.value.name}_副本`
    form.params = template.value.params.reduce((acc, p) => {
      acc[p.name] = p.default
      return acc
    }, {} as Record<string, any>)
  } catch {
    Message.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const loadTags = async () => {
  loadingTags.value = true
  try {
    const res = await strategyApi.getTags()
    tags.value = res.data || []
  } catch {
  } finally {
    loadingTags.value = false
  }
}

const handleSubmit = async () => {
  if (!template.value) return

  submitting.value = true
  try {
    const res = await strategyApi.createFromTemplate({
      template_id: template.value.id,
      name: form.name,
      description: form.description || undefined,
      params: form.params,
      tag_ids: form.tag_ids
    })

    Message.success('策略创建成功')
    router.push({
      name: 'StrategyEditor',
      params: { id: res.data.id }
    })
  } catch (err: any) {
    Message.error(err?.message || '创建策略失败')
  } finally {
    submitting.value = false
  }
}

const handleBack = () => {
  router.push({ name: 'StrategyTemplates' })
}

onMounted(() => {
  loadTemplate()
  loadTags()
})
</script>