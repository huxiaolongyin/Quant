<template>
  <div class="min-h-screen flex flex-col">
    <div class="page-header-with-subtitle">
      <p class="page-subtitle mt-1">可视化配置选股条件，筛选目标股票池</p>
      <a-button type="primary" size="large" class="rounded-lg" @click="handleCreate">
        <template #icon>
          <span class="material-symbols-outlined text-base">add</span>
        </template>
        新建选股器
      </a-button>
    </div>

    <div class="flex items-center gap-4 mb-8">
      <a-input-search
        v-model="searchName"
        placeholder="搜索选股器名称..."
        class="w-64"
        @search="loadData"
      />
      <a-radio-group v-model="filterActive" type="button" @change="loadData">
        <a-radio value="all" class="w-24">全部</a-radio>
        <a-radio :value="true">已启用</a-radio>
        <a-radio :value="false">已停用</a-radio>
      </a-radio-group>
    </div>

    <div v-if="loading" class="empty-state">
      <a-spin dot />
    </div>

    <div v-else-if="list.length === 0" class="empty-state">
      <span class="material-symbols-outlined text-6xl mb-4">filter_alt</span>
      <p>暂无选股器，点击右上角按钮创建</p>
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
            <span class="truncate pr-2 text-slate-900 dark:text-white" :title="item.name"
              >{{ item.name }}
            </span>
            <a-tag v-if="item.isActive" color="green" size="small" bordered>启用</a-tag>
            <a-tag v-else color="gray" size="small" bordered>停用</a-tag>
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
              <template #icon>
                <span class="material-symbols-outlined text-base"> more_vert </span>
              </template>
            </a-button>
            <template #content>
              <a-doption @click.stop="handleExecute(item.id)">
                <span class="material-symbols-outlined text-base mr-1">play_arrow</span>
                执行选股
              </a-doption>
              <a-doption @click.stop="handleCopy(item)">
                <span class="material-symbols-outlined text-base mr-1">content_copy</span>
                复制
              </a-doption>
              <a-doption class="!text-danger" @click.stop="handleDelete(item.id)">
                <span class="material-symbols-outlined text-base mr-1">delete</span> 删除
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
            <div class="text-xs text-slate-400 mb-1">执行次数</div>
            <div class="font-bold text-lg text-slate-700 dark:text-slate-200">
              {{ item.resultCount }}
            </div>
          </div>
          <div class="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
          <div class="text-center">
            <div class="text-xs text-slate-400 mb-1">最近结果</div>
            <div class="font-bold text-lg text-slate-700 dark:text-slate-200">
              {{ item.lastResultCount ?? "-" }}
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center mt-2">
          <span class="text-xs text-slate-400">{{
            item.lastResultDate || "未执行"
          }}</span>
          <span class="text-xs text-slate-400">{{ item.updatedAt?.split(" ")[0] }}</span>
        </div>
      </a-card>
    </div>

    <div v-if="total > pageSize" class="flex justify-center mt-6">
      <a-pagination
        :current="page"
        :page-size="pageSize"
        :total="total"
        show-total
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { selectorApi, SelectorListItem } from "@/api/selector";
import { Message, Modal } from "@arco-design/web-vue";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loading = ref(false);
const list = ref<SelectorListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(12);
const searchName = ref("");
const filterActive = ref<string | boolean>("all");

const loadData = async () => {
  loading.value = true;
  try {
    const res = await selectorApi.getList({
      page: page.value,
      pageSize: pageSize.value,
      name: searchName.value || undefined,
      isActive:
        filterActive.value === "all"
          ? undefined
          : filterActive.value === "true" || filterActive.value === true,
    });
    list.value = res.data.list;
    total.value = res.data.total;
  } catch {
    Message.error("获取列表失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadData();
};

const handleCreate = () => {
  router.push({ name: "SelectorEditor" });
};

const handleEdit = (id: number) => {
  router.push({ name: "SelectorEditor", params: { id } });
};

const handleExecute = async (id: number) => {
  router.push({ name: "SelectorEditor", params: { id }, query: { execute: "1" } });
};

const handleCopy = async (item: SelectorListItem) => {
  router.push({ name: "SelectorEditor", query: { copy: item.id } });
};

const handleDelete = async (id: number) => {
  Modal.confirm({
    title: "确认删除",
    content: "删除后无法恢复，确定要删除该选股器吗？",
    okText: "删除",
    cancelText: "取消",
    onOk: async () => {
      try {
        await selectorApi.delete(id);
        Message.success("删除成功");
        loadData();
      } catch {
        Message.error("删除失败");
      }
    },
  });
};

onMounted(() => {
  loadData();
});
</script>
