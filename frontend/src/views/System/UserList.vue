<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
      <a-button type="primary" @click="openCreateModal">
        <template #icon><icon-plus /></template>
        新增用户
      </a-button>
    </div>

    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex gap-4 mb-6">
        <a-input
          v-model="searchForm.username"
          placeholder="用户名"
          allow-clear
          style="width: 200px"
          @press-enter="fetchUsers"
        />
        <a-select
          v-model="searchForm.status"
          placeholder="状态"
          allow-clear
          style="width: 120px"
          @change="fetchUsers"
        >
          <a-option :value="1">启用</a-option>
          <a-option :value="0">禁用</a-option>
        </a-select>
        <a-button type="primary" @click="fetchUsers">搜索</a-button>
      </div>

      <a-table
        :data="users"
        :loading="loading"
        :pagination="pagination"
        @page-change="onPageChange"
      >
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="80" />
          <a-table-column title="用户名" data-index="username" />
          <a-table-column title="昵称" data-index="nickname" />
          <a-table-column title="邮箱" data-index="email" />
          <a-table-column title="角色">
            <template #cell="{ record }">
              <a-tag v-for="role in record.roles" :key="role.id" color="arcoblue">{{
                role.name
              }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <a-tag :color="record.status === 1 ? 'green' : 'red'">
                {{ record.status === 1 ? "启用" : "禁用" }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="createdAt" :width="180" />
          <a-table-column title="操作" :width="150">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="openEditModal(record)"
                  >编辑</a-button
                >
                <a-popconfirm content="确定删除该用户吗？" @ok="deleteUser(record.id)">
                  <a-button type="text" size="small" status="danger">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:visible="modalVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      @ok="handleSubmit"
      @cancel="resetForm"
    >
      <a-form ref="formRef" :model="form" :rules="rules" layout="vertical">
        <a-form-item field="username" label="用户名">
          <a-input
            v-model="form.username"
            :disabled="isEdit"
            placeholder="请输入用户名"
          />
        </a-form-item>
        <a-form-item v-if="!isEdit" field="password" label="密码">
          <a-input-password v-model="form.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item field="email" label="邮箱">
          <a-input v-model="form.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item field="nickname" label="昵称">
          <a-input v-model="form.nickname" placeholder="请输入昵称" />
        </a-form-item>
        <a-form-item field="phone" label="手机号">
          <a-input v-model="form.phone" placeholder="请输入手机号" />
        </a-form-item>
        <a-form-item field="status" label="状态">
          <a-radio-group v-model="form.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item field="roleIds" label="角色">
          <a-select v-model="form.roleIds" multiple placeholder="请选择角色">
            <a-option v-for="role in roles" :key="role.id" :value="role.id">{{
              role.name
            }}</a-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { roleApi, userApi } from "@/api/user";
import type { RoleInfo, UserInfo } from "@/types/user";
import { Message } from "@arco-design/web-vue";
import { IconPlus } from "@arco-design/web-vue/es/icon";
import { onMounted, reactive, ref } from "vue";

const loading = ref(false);
const users = ref<UserInfo[]>([]);
const roles = ref<RoleInfo[]>([]);
const modalVisible = ref(false);
const isEdit = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref();

const searchForm = reactive({
  username: "",
  status: undefined as number | undefined,
});

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const form = reactive({
  username: "",
  password: "",
  email: "",
  nickname: "",
  phone: "",
  status: 1,
  roleIds: [] as number[],
});

const rules = {
  username: [{ required: true, message: "请输入用户名" }],
  password: [{ required: true, message: "请输入密码" }],
  email: [
    { required: true, message: "请输入邮箱" },
    { type: "email", message: "邮箱格式不正确" },
  ],
};

async function fetchUsers() {
  loading.value = true;
  try {
    const res = await userApi.getList({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...searchForm,
    });
    if (res.code === 200) {
      users.value = res.data.list;
      console.log(users.value);
      pagination.total = res.data.total;
    }
  } finally {
    loading.value = false;
  }
}

async function fetchRoles() {
  const res = await roleApi.getAll();
  if (res.code === 200) {
    roles.value = res.data;
  }
}

function onPageChange(page: number) {
  pagination.current = page;
  fetchUsers();
}

function openCreateModal() {
  isEdit.value = false;
  editingId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEditModal(user: UserInfo) {
  isEdit.value = true;
  editingId.value = user.id;
  Object.assign(form, {
    username: user.username,
    email: user.email,
    nickname: user.nickname || "",
    phone: user.phone || "",
    status: user.status,
    roleIds: user.roles.map((r) => r.id),
  });
  modalVisible.value = true;
}

function resetForm() {
  Object.assign(form, {
    username: "",
    password: "",
    email: "",
    nickname: "",
    phone: "",
    status: 1,
    roleIds: [],
  });
  formRef.value?.resetFields();
}

async function handleSubmit() {
  try {
    await formRef.value?.validate();
    if (isEdit.value && editingId.value) {
      const res = await userApi.update(editingId.value, {
        email: form.email,
        nickname: form.nickname,
        phone: form.phone,
        status: form.status,
        roleIds: form.roleIds,
      });
      if (res.code === 200) {
        Message.success("更新成功");
        modalVisible.value = false;
        fetchUsers();
      }
    } else {
      const res = await userApi.create(form);
      if (res.code === 200) {
        Message.success("创建成功");
        modalVisible.value = false;
        fetchUsers();
      }
    }
  } catch {
    // validation failed
  }
}

async function deleteUser(id: number) {
  const res = await userApi.delete(id);
  if (res.code === 200) {
    Message.success("删除成功");
    fetchUsers();
  }
}

onMounted(() => {
  fetchUsers();
  fetchRoles();
});
</script>
