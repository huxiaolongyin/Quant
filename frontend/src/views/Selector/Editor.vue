<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <a-button @click="router.back()">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <h2 class="text-xl font-semibold">{{ isEdit ? "编辑选股器" : "新建选股器" }}</h2>
      </div>
      <div class="flex gap-3">
        <a-button
          type="outline"
          status="success"
          :loading="executing"
          :disabled="hasUnsavedChanges"
          @click="handleExecute"
        >
          <template #icon><icon-play-arrow /></template>
          执行选股
        </a-button>
        <a-button type="primary" :loading="saving" @click="handleSave">
          <template #icon><icon-save /></template>
          保存
        </a-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-lg shadow-sm p-6">
        <a-form :model="form" layout="vertical">
          <a-form-item label="选股器名称" required>
            <a-input v-model="form.name" placeholder="请输入选股器名称" />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea
              v-model="form.description"
              placeholder="请输入描述"
              :max-length="200"
              show-word-limit
            />
          </a-form-item>
        </a-form>

        <div class="mt-6">
          <ConditionBuilder v-model="form.rule" />
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-medium">执行结果</h3>
          <span v-if="executeResult" class="text-sm text-gray-500">
            耗时: {{ executeResult.executionTime }}ms
          </span>
        </div>

        <div v-if="executing" class="flex justify-center py-20">
          <a-spin dot tip="正在执行选股..." />
        </div>

        <div v-else-if="!executeResult" class="text-gray-400 text-center py-20">
          点击"执行选股"按钮查看筛选结果
        </div>

        <div v-else>
          <div class="flex items-center gap-4 mb-4 p-4 bg-blue-50 rounded-lg">
            <div class="text-center">
              <div class="text-xs text-gray-500">选股日期</div>
              <div class="font-bold text-blue-600">{{ executeResult.tradeDate }}</div>
            </div>
            <div class="w-px h-8 bg-blue-200"></div>
            <div class="text-center">
              <div class="text-xs text-gray-500">筛选结果</div>
              <div class="font-bold text-blue-600">{{ executeResult.count }} 只</div>
            </div>
          </div>

          <a-input-search
            v-model="stockSearch"
            placeholder="搜索股票代码或名称..."
            class="mb-4"
          />

          <a-table
            :data="filteredStocks"
            :pagination="{ pageSize: 10 }"
            :bordered="false"
            size="small"
          >
            <template #columns>
              <a-table-column title="股票代码" data-index="full_stock_code" />
              <a-table-column title="股票名称" data-index="short_name" />
              <a-table-column title="行业" data-index="industry" />
            </template>
          </a-table>
        </div>
      </div>
    </div>

    <div v-if="isEdit" class="mt-6 bg-white rounded-lg shadow-sm p-6">
      <h3 class="font-medium mb-4">历史执行记录</h3>
      <a-table
        :data="historyResults"
        :loading="loadingHistory"
        :pagination="{ pageSize: 5 }"
        :bordered="false"
        size="small"
      >
        <template #columns>
          <a-table-column title="执行日期" data-index="tradeDate" />
          <a-table-column title="结果数量">
            <template #cell="{ record }">
              <a-tag color="blue">{{ record.count }} 只</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="耗时" data-index="executionTime">
            <template #cell="{ record }">{{ record.executionTime }}ms</template>
          </a-table-column>
          <a-table-column title="操作">
            <template #cell="{ record }">
              <a-button type="text" size="small" @click="viewResult(record)">
                查看详情
              </a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ConditionNode, selectorApi, SelectorResult } from "@/api/selector";
import ConditionBuilder from "@/components/Selector/ConditionBuilder.vue";
import { Message } from "@arco-design/web-vue";
import { IconLeft, IconPlayArrow, IconSave } from "@arco-design/web-vue/es/icon";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const selectorId = computed(() => {
  const id = route.params.id;
  return id ? Number(id) : null;
});

const isEdit = computed(() => !!selectorId.value);

const form = ref<{
  name: string;
  description: string;
  rule: ConditionNode;
}>({
  name: "",
  description: "",
  rule: {
    nodeType: "group",
    logic: "and",
    children: [],
  },
});

const hasUnsavedChanges = ref(false);

watch(
  () => [form.value.name, form.value.description, form.value.rule],
  () => {
    hasUnsavedChanges.value = true;
  },
  { deep: true }
);

const saving = ref(false);
const executing = ref(false);
const executeResult = ref<{
  selectorId: number;
  tradeDate: string;
  stockCodes: string[];
  count: number;
  executionTime: number;
  stocks?: { full_stock_code: string; short_name: string; industry?: string }[];
} | null>(null);

const stockSearch = ref("");
const loadingHistory = ref(false);
const historyResults = ref<SelectorResult[]>([]);

const filteredStocks = computed(() => {
  if (!executeResult.value?.stocks) return [];
  const search = stockSearch.value.toLowerCase();
  if (!search) return executeResult.value.stocks;
  return executeResult.value.stocks.filter(
    (s) =>
      s.full_stock_code.toLowerCase().includes(search) ||
      s.short_name.toLowerCase().includes(search)
  );
});

const loadSelector = async () => {
  if (!selectorId.value) return;

  try {
    const res = await selectorApi.getById(selectorId.value);
    form.value = {
      name: res.data.name,
      description: res.data.description || "",
      rule: res.data.rule || { nodeType: "group", logic: "and", children: [] },
    };
    hasUnsavedChanges.value = false;
  } catch {
    Message.error("获取选股器详情失败");
    router.back();
  }
};

const loadHistory = async () => {
  if (!selectorId.value) return;

  loadingHistory.value = true;
  try {
    const res = await selectorApi.getResults(selectorId.value, { page: 1, pageSize: 10 });
    historyResults.value = res.data.list;
  } catch {
    console.error("Failed to load history");
  } finally {
    loadingHistory.value = false;
  }
};

const handleSave = async () => {
  if (!form.value.name) {
    Message.warning("请输入选股器名称");
    return;
  }

  if (!form.value.rule.children?.length) {
    Message.warning("请至少添加一个筛选条件");
    return;
  }

  saving.value = true;
  try {
    if (isEdit.value && selectorId.value) {
      await selectorApi.update(selectorId.value, {
        name: form.value.name,
        description: form.value.description,
        rule: form.value.rule,
      });
      Message.success("更新成功");
    } else {
      const res = await selectorApi.create({
        name: form.value.name,
        description: form.value.description,
        rule: form.value.rule,
      });
      Message.success("创建成功");
      router.replace({ name: "SelectorEditor", params: { id: res.data.id } });
    }
    hasUnsavedChanges.value = false;
  } catch {
    Message.error("保存失败");
  } finally {
    saving.value = false;
  }
};

const handleExecute = async () => {
  if (!form.value.rule.children?.length) {
    Message.warning("请至少添加一个筛选条件");
    return;
  }

  executing.value = true;
  try {
    if (isEdit.value && selectorId.value) {
      const res = await selectorApi.execute(selectorId.value);
      executeResult.value = res.data;
    } else {
      const tempSelector = await selectorApi.create({
        name: form.value.name || "临时选股器",
        description: form.value.description,
        rule: form.value.rule,
      });
      const res = await selectorApi.execute(tempSelector.data.id);
      executeResult.value = res.data;

      if (!isEdit.value) {
        await selectorApi.update(tempSelector.data.id, { name: form.value.name });
      }
    }
    Message.success(`选股完成，共筛选出 ${executeResult.value?.count} 只股票`);
  } catch {
    Message.error("执行选股失败");
  } finally {
    executing.value = false;
  }
};

const viewResult = async (result: SelectorResult) => {
  if (!selectorId.value) return;
  
  executing.value = true;
  try {
    const res = await selectorApi.getResultById(selectorId.value, result.id);
    executeResult.value = {
      selectorId: res.data.selectorId,
      tradeDate: res.data.tradeDate,
      stockCodes: res.data.stockCodes,
      count: res.data.count,
      executionTime: res.data.executionTime || 0,
      stocks: res.data.stocks,
    };
    stockSearch.value = "";
  } catch {
    Message.error("获取选股结果详情失败");
  } finally {
    executing.value = false;
  }
};

onMounted(() => {
  if (isEdit.value) {
    loadSelector();
    loadHistory();
  }

  if (route.query.execute === "1" && selectorId.value) {
    handleExecute();
  }
});
</script>
