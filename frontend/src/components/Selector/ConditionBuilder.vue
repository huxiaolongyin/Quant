<template>
  <div class="condition-builder">
    <div class="flex items-center justify-between mb-3">
      <span class="font-medium text-gray-700">选股条件</span>
      <a-button size="small" @click="addCondition">
        <template #icon><icon-plus /></template>
        添加条件
      </a-button>
    </div>

    <div
      v-if="!localRule.children?.length"
      class="text-gray-400 text-center py-8 border-2 border-dashed border-gray-200 rounded-lg"
    >
      点击上方按钮添加筛选条件
    </div>

    <div v-else class="space-y-2">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-sm text-gray-500">条件关系:</span>
        <a-radio-group v-model="localRule.logic" type="button" size="small">
          <a-radio value="and" class="w-24">且 (AND)</a-radio>
          <a-radio value="or">或 (OR)</a-radio>
        </a-radio-group>
      </div>

      <div
        v-for="(child, index) in localRule.children"
        :key="index"
        class="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg group"
      >
        <div class="flex-1 grid grid-cols-12 gap-2">
          <a-select
            v-model="child.field"
            placeholder="选择字段"
            class="col-span-3"
            @change="onFieldChange(child)"
          >
            <a-optgroup label="基础字段">
              <a-option
                v-for="f in basicFields"
                :key="f.name"
                :value="f.name"
                :label="f.label"
              />
            </a-optgroup>
            <a-optgroup label="行情指标">
              <a-option
                v-for="f in quoteFields"
                :key="f.name"
                :value="f.name"
                :label="f.label"
              />
            </a-optgroup>
            <a-optgroup label="技术指标">
              <a-option
                v-for="f in indicatorFields"
                :key="f.name"
                :value="f.name"
                :label="f.label"
              />
            </a-optgroup>
          </a-select>

          <a-select v-model="child.operator" placeholder="操作符" class="col-span-2">
            <a-option
              v-for="op in getOperators(child.field)"
              :key="op.value"
              :value="op.value"
              :label="op.label"
            />
          </a-select>

          <div class="col-span-7">
            <a-select
              v-if="getFieldOptions(child.field, index)?.length"
              v-model="child.value"
              placeholder="选择值"
              :multiple="['in', 'not_in'].includes(child.operator || '')"
              allow-clear
              allow-search
            >
              <a-option
                v-for="opt in getFieldOptions(child.field, index)"
                :key="opt.value"
                :value="opt.value"
                :label="opt.label"
              />
            </a-select>
            <a-input-number
              v-else-if="getFieldDataType(child.field) === 'number'"
              v-model="child.value"
              placeholder="输入数值"
              class="w-full"
            />
            <a-input v-else v-model="child.value" placeholder="输入值" />
          </div>
        </div>

        <a-button
          type="text"
          status="danger"
          size="small"
          class="opacity-0 group-hover:opacity-100 transition-opacity"
          @click="removeCondition(index)"
        >
          <template #icon><icon-delete /></template>
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ConditionNode, FieldOption, selectorApi, SelectorField } from "@/api/selector";
import { IconDelete, IconPlus } from "@arco-design/web-vue/es/icon";
import { computed, onMounted, ref, watch } from "vue";

const props = defineProps<{
  modelValue: ConditionNode;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: ConditionNode): void;
}>();

const fields = ref<SelectorField[]>([]);
const isInternalUpdate = ref(false);
const dynamicOptions = ref<Record<string, FieldOption[]>>({});

const localRule = ref<ConditionNode>({
  nodeType: "group",
  logic: "and",
  children: [],
});

const basicFields = computed(() => fields.value.filter((f) => f.fieldType === "basic"));
const quoteFields = computed(() => fields.value.filter((f) => f.fieldType === "quote"));
const indicatorFields = computed(() =>
  fields.value.filter((f) => f.fieldType === "indicator")
);

const dynamicFields = ["industry", "province", "city"];

const operatorLabels: Record<string, string> = {
  eq: "等于",
  ne: "不等于",
  gt: "大于",
  gte: "大于等于",
  lt: "小于",
  lte: "小于等于",
  in: "在列表中",
  not_in: "不在列表中",
  contains: "包含",
  not_contains: "不包含",
  like: "模糊匹配",
  between: "区间",
};

const getOperators = (fieldName: string | undefined) => {
  if (!fieldName) return [];
  const field = fields.value.find((f) => f.name === fieldName);
  if (!field) return [];
  return field.operators.map((op) => ({
    value: op,
    label: operatorLabels[op] || op,
  }));
};

const getFieldOptions = (fieldName: string | undefined, index?: number) => {
  if (!fieldName) return null;
  const field = fields.value.find((f) => f.name === fieldName);
  if (field?.options) return field.options;
  if (dynamicFields.includes(fieldName)) {
    if (fieldName === "city" && index !== undefined) {
      const provinceValue = findProvinceValue(index);
      const cacheKey = provinceValue ? `city_${provinceValue}` : "city";
      return dynamicOptions.value[cacheKey] || [];
    }
    return dynamicOptions.value[fieldName] || [];
  }
  return null;
};

const getFieldDataType = (fieldName: string | undefined) => {
  if (!fieldName) return "string";
  const field = fields.value.find((f) => f.name === fieldName);
  return field?.dataType || "string";
};

const findProvinceValue = (currentIndex: number): string | undefined => {
  const children = localRule.value.children;
  if (!children) return undefined;
  for (let i = 0; i < currentIndex; i++) {
    const child = children[i];
    if (child.field === "province" && child.value) {
      return child.value as string;
    }
  }
  return undefined;
};

const loadDynamicOptions = async (field: string, province?: string) => {
  if (field === "city" && province) {
    const cacheKey = `city_${province}`;
    if (dynamicOptions.value[cacheKey]) return;
    try {
      const res = await selectorApi.getOptions("city", province);
      dynamicOptions.value[cacheKey] = res.data;
    } catch {
      console.error(`Failed to load city options for province: ${province}`);
    }
  } else if (dynamicFields.includes(field)) {
    if (dynamicOptions.value[field]) return;
    try {
      const res = await selectorApi.getOptions(field as "industry" | "province" | "city");
      dynamicOptions.value[field] = res.data;
    } catch {
      console.error(`Failed to load ${field} options`);
    }
  }
};

const onFieldChange = async (child: ConditionNode) => {
  child.operator = undefined;
  child.value = undefined;
  const ops = getOperators(child.field);
  if (ops.length > 0) {
    child.operator = ops[0].value;
  }
  if (child.field && dynamicFields.includes(child.field)) {
    await loadDynamicOptions(child.field);
  }
};

const addCondition = async () => {
  if (!localRule.value.children) {
    localRule.value.children = [];
  }
  localRule.value.children.push({
    nodeType: "condition",
    field: undefined,
    operator: undefined,
    value: undefined,
  });
};

const removeCondition = (index: number) => {
  localRule.value.children?.splice(index, 1);
};

const loadFields = async () => {
  try {
    const res = await selectorApi.getFields();
    fields.value = res.data;
  } catch {
    console.error("Failed to load fields");
  }
};

watch(
  () => props.modelValue,
  (val) => {
    if (isInternalUpdate.value) {
      isInternalUpdate.value = false;
      return;
    }
    if (val) {
      localRule.value = JSON.parse(JSON.stringify(val));
    }
  },
  { immediate: true, deep: true }
);

watch(
  localRule,
  (val) => {
    isInternalUpdate.value = true;
    emit("update:modelValue", JSON.parse(JSON.stringify(val)));
  },
  { deep: true }
);

watch(
  () => localRule.value.children,
  async (children) => {
    if (!children) return;
    for (const child of children) {
      if (child.field === "city") {
        const provinceValue = findProvinceValue(children.indexOf(child));
        if (provinceValue) {
          await loadDynamicOptions("city", provinceValue);
        }
      }
    }
  },
  { deep: true }
);

onMounted(async () => {
  await loadFields();
  await Promise.all([
    loadDynamicOptions("industry"),
    loadDynamicOptions("province"),
    loadDynamicOptions("city"),
  ]);
});
</script>
