<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">角色管理</h1>
      <a-button type="primary" @click="openCreateModal">
        <template #icon><icon-plus /></template>
        新增角色
      </a-button>
    </div>

    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex gap-4 mb-6">
        <a-input v-model="searchForm.name" placeholder="角色名称" allow-clear style="width: 200px" @press-enter="fetchRoles" />
        <a-select v-model="searchForm.status" placeholder="状态" allow-clear style="width: 120px" @change="fetchRoles">
          <a-option :value="1">启用</a-option>
          <a-option :value="0">禁用</a-option>
        </a-select>
        <a-button type="primary" @click="fetchRoles">搜索</a-button>
      </div>

      <a-table :data="roles" :loading="loading" :pagination="pagination" @page-change="onPageChange">
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="80" />
          <a-table-column title="角色名称" data-index="name" />
          <a-table-column title="角色编码" data-index="code" />
          <a-table-column title="描述" data-index="description" />
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <a-tag :color="record.status === 1 ? 'green' : 'red'">
                {{ record.status === 1 ? '启用' : '禁用' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="createdAt" :width="180" />
          <a-table-column title="操作" :width="150">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="openEditModal(record)">编辑</a-button>
                <a-popconfirm content="确定删除该角色吗？" @ok="deleteRole(record.id)">
                  <a-button type="text" size="small" status="danger" :disabled="record.code === 'admin'">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>

    <a-modal v-model:visible="modalVisible" :title="isEdit ? '编辑角色' : '新增角色'" @ok="handleSubmit" @cancel="resetForm" width="600px">
      <a-form ref="formRef" :model="form" :rules="rules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item field="name" label="角色名称">
              <a-input v-model="form.name" placeholder="请输入角色名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item field="code" label="角色编码">
              <a-input v-model="form.code" :disabled="isEdit" placeholder="请输入角色编码" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item field="description" label="描述">
          <a-textarea v-model="form.description" placeholder="请输入描述" />
        </a-form-item>
        <a-form-item field="status" label="状态">
          <a-radio-group v-model="form.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item field="permissionIds" label="权限">
          <div class="border rounded p-4 max-h-60 overflow-y-auto">
            <div v-for="(perms, module) in permissionsByModule" :key="module" class="mb-4">
              <div class="font-medium text-gray-700 mb-2">{{ getModuleName(module) }}</div>
              <a-checkbox-group v-model="form.permissionIds">
                <a-checkbox v-for="perm in perms" :key="perm.id" :value="perm.id">
                  {{ perm.name }}
                </a-checkbox>
              </a-checkbox-group>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import { roleApi } from '@/api/user'
import type { RoleInfo, PermissionInfo } from '@/types/user'

const loading = ref(false)
const roles = ref<RoleInfo[]>([])
const permissionsByModule = ref<Record<string, PermissionInfo[]>>({})
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref()

const searchForm = reactive({
  name: '',
  status: undefined as number | undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  description: '',
  status: 1,
  sort: 0,
  permissionIds: [] as number[]
})

const rules = {
  name: [{ required: true, message: '请输入角色名称' }],
  code: [{ required: true, message: '请输入角色编码' }]
}

const moduleNameMap: Record<string, string> = {
  system: '系统管理',
  trading: '交易管理',
  data: '数据管理'
}

function getModuleName(module: string): string {
  return moduleNameMap[module] || module
}

async function fetchRoles() {
  loading.value = true
  try {
    const res = await roleApi.getList({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...searchForm
    })
    if (res.code === 200) {
      roles.value = res.data.list
      pagination.total = res.data.total
    }
  } finally {
    loading.value = false
  }
}

async function fetchPermissions() {
  const res = await roleApi.getPermissionsByModule()
  if (res.code === 200) {
    permissionsByModule.value = res.data
  }
}

function onPageChange(page: number) {
  pagination.current = page
  fetchRoles()
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  modalVisible.value = true
}

async function openEditModal(role: RoleInfo) {
  isEdit.value = true
  editingId.value = role.id
  
  const res = await roleApi.getDetail(role.id)
  if (res.code === 200) {
    Object.assign(form, {
      name: res.data.name,
      code: res.data.code,
      description: res.data.description || '',
      status: res.data.status,
      sort: res.data.sort,
      permissionIds: res.data.permissions.map(p => p.id)
    })
  }
  modalVisible.value = true
}

function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    description: '',
    status: 1,
    sort: 0,
    permissionIds: []
  })
  formRef.value?.resetFields()
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    if (isEdit.value && editingId.value) {
      const res = await roleApi.update(editingId.value, {
        name: form.name,
        description: form.description,
        status: form.status,
        sort: form.sort,
        permissionIds: form.permissionIds
      })
      if (res.code === 200) {
        Message.success('更新成功')
        modalVisible.value = false
        fetchRoles()
      }
    } else {
      const res = await roleApi.create(form)
      if (res.code === 200) {
        Message.success('创建成功')
        modalVisible.value = false
        fetchRoles()
      }
    }
  } catch {
    // validation failed
  }
}

async function deleteRole(id: number) {
  const res = await roleApi.delete(id)
  if (res.code === 200) {
    Message.success('删除成功')
    fetchRoles()
  }
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>