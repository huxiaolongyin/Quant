<template>
  <div class="h-full flex flex-col bg-background-light dark:bg-background-dark">
    <header
      class="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-background-dark z-10"
    >
      <div class="flex items-center gap-4">
        <a-button type="text" shape="circle" @click="handleBack">
          <template #icon
            ><span class="material-symbols-outlined">arrow_back</span></template
          >
        </a-button>

        <div class="flex flex-col">
          <a-input
            v-model="form.name"
            placeholder="请输入策略名称"
            class="!bg-transparent !border-none !px-0 !h-auto text-lg font-bold text-slate-800 dark:text-white focus:!bg-slate-100 dark:focus:!bg-slate-800"
          />
          <span class="text-xs text-slate-400" v-if="form.updated_at"
            >上次保存: {{ form.updated_at }}</span
          >
        </div>
      </div>

      <a-space>
        <a-button @click="handleSave" :loading="saving">
          <template #icon
            ><span class="material-symbols-outlined text-base">save</span></template
          >
          保存
        </a-button>
        <a-button type="primary" status="success" @click="handleRun" :loading="running">
          <template #icon
            ><span class="material-symbols-outlined text-base">play_arrow</span></template
          >
          运行回测
        </a-button>
      </a-space>
    </header>

    <div class="flex-1 flex flex-col overflow-hidden">
      <div class="flex-1 flex flex-col bg-[#0d1117] rounded-none border-0 shadow-none">
        <div
          class="h-12 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4"
        >
          <div class="flex items-center gap-4">
            <div
              class="flex items-center gap-2 px-3 py-1.5 bg-[#0d1117] border-x border-t border-slate-800 rounded-t-lg -mb-[13px]"
            >
              <span class="material-symbols-outlined text-sm text-amber-500"
                >description</span
              >
              <span class="text-xs font-medium text-slate-300">{{ fileName }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="validating"
              class="px-3 py-1.5 text-xs font-medium text-blue-400 flex items-center gap-1.5"
            >
              <a-spin size="mini" />
              验证中...
            </button>
            <button
              v-else-if="codeErrors.length > 0"
              class="px-3 py-1.5 text-xs font-medium text-red-400 flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">error</span>
              {{ codeErrors.length }} 个错误
            </button>
            <button
              v-else-if="codeWarnings.length > 0"
              class="px-3 py-1.5 text-xs font-medium text-orange-400 flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">warning</span>
              {{ codeWarnings.length }} 个警告
            </button>
            <button
              v-else-if="form.code"
              class="px-3 py-1.5 text-xs font-medium text-emerald-400 flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">check_circle</span>
              代码安全
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-hidden">
          <MonacoEditor
            ref="editorRef"
            :model-value="form.code ?? ''"
            language="python"
            @cursor-change="handleCursorChange"
            @ready="handleEditorReady"
          />
        </div>

        <div
          class="h-6 bg-primary px-4 flex items-center justify-between text-[10px] font-bold text-white uppercase"
        >
          <div class="flex items-center gap-4">
            <span>{{ running ? "Running" : "Ready" }}</span>
            <span>UTF-8</span>
            <span>Python 3.10</span>
          </div>
          <div class="flex items-center gap-4">
            <span
              >Ln {{ cursorPosition.lineNumber }}, Col {{ cursorPosition.column }}</span
            >
            <span>Spaces: 4</span>
          </div>
        </div>
      </div>

      <div
        class="border-t border-slate-800 bg-slate-900 transition-all duration-300 overflow-hidden"
        :style="{ height: showConsole ? consoleHeight + 'px' : '24px' }"
      >
        <div
          class="h-6 flex items-center justify-between px-4 cursor-pointer hover:bg-slate-800 transition-colors"
          @click="toggleConsole"
        >
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-slate-500 text-sm">{{
              showConsole ? "expand_more" : "expand_less"
            }}</span>
            <span class="text-xs text-slate-400 font-medium">控制台输出</span>
            <span
              v-if="codeErrors.length > 0"
              class="text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded"
            >
              {{ codeErrors.length }} 错误
            </span>
            <span
              v-else-if="codeWarnings.length > 0"
              class="text-[10px] bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded"
            >
              {{ codeWarnings.length }} 警告
            </span>
          </div>
          <div v-if="showConsole" class="flex items-center gap-1">
            <a-button type="text" size="mini" @click.stop="logs = ''">
              <template #icon>
                <span class="material-symbols-outlined text-sm text-slate-400"
                  >delete</span
                >
              </template>
            </a-button>
          </div>
        </div>

        <div
          v-show="showConsole"
          class="overflow-y-auto bg-[#1e1e1e] font-mono text-xs"
          :style="{ height: consoleHeight - 24 + 'px' }"
        >
          <div class="p-4">
            <div
              v-if="
                showValidationPanel && (codeErrors.length > 0 || codeWarnings.length > 0)
              "
              class="mb-4 p-3 rounded bg-slate-800"
            >
              <div class="flex justify-between items-center mb-2">
                <span class="text-slate-300 font-bold">代码验证结果</span>
                <a-button type="text" size="mini" @click="showValidationPanel = false">
                  <template #icon>
                    <span class="material-symbols-outlined text-sm">close</span>
                  </template>
                </a-button>
              </div>
              <div v-if="codeErrors.length > 0" class="mb-2">
                <div class="text-red-400 mb-1">错误:</div>
                <div v-for="(err, i) in codeErrors" :key="i" class="text-red-300 pl-2">
                  • {{ err }}
                </div>
              </div>
              <div v-if="codeWarnings.length > 0">
                <div class="text-orange-400 mb-1">警告:</div>
                <div
                  v-for="(warn, i) in codeWarnings"
                  :key="i"
                  class="text-orange-300 pl-2"
                >
                  • {{ warn }}
                </div>
              </div>
            </div>

            <div v-if="!logs && !running" class="text-gray-500 text-center py-6">
              暂无运行日志
            </div>
            <div v-else class="whitespace-pre-wrap text-green-400">{{ logs }}</div>
            <div v-if="running" class="mt-2 text-blue-400 animate-pulse">
              > 正在执行策略回测...
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { strategyApi } from "@/api/strategy";
import MonacoEditor from "@/components/Editor/MonacoEditor.vue";
import type { StrategyCreateRequest, StrategyDetail } from "@/types/strategy";
import { Message } from "@arco-design/web-vue";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const saving = ref(false);
const running = ref(false);
const validating = ref(false);
const showConsole = ref(true);
const showValidationPanel = ref(false);
const logs = ref("");
const consoleHeight = ref(200);

const codeErrors = ref<string[]>([]);
const codeWarnings = ref<string[]>([]);

const editorRef = ref<InstanceType<typeof MonacoEditor>>();
const cursorPosition = ref({ lineNumber: 1, column: 1 });

const form = reactive<Partial<StrategyDetail>>({
  id: "",
  name: "",
  code: "",
  description: "",
  parameters: {},
  tags: [],
  updated_at: "",
});

const isEdit = computed(() => !!route.params.id);
const copyFrom = route.query.copyFrom as string | undefined;
const copyName = route.query.name as string | undefined;

const fileName = computed(() => {
  if (form.name) {
    return form.name.toLowerCase().replace(/\s+/g, "_") + ".py";
  }
  return "main.py";
});

let validateTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => form.code,
  (code) => {
    if (!code) {
      codeErrors.value = [];
      codeWarnings.value = [];
      editorRef.value?.clearMarkers();
      return;
    }
    if (validateTimer) clearTimeout(validateTimer);
    validateTimer = setTimeout(async () => {
      validating.value = true;
      try {
        const res = await strategyApi.validateCode(code);
        codeErrors.value = res.errors || [];
        codeWarnings.value = res.warnings || [];

        if (editorRef.value && (res.errors?.length || res.warnings?.length)) {
          const markers = [
            ...(res.errors || []).map((err: string) => ({
              line: extractLineNumber(err) || 1,
              message: err,
              severity: "error" as const,
            })),
            ...(res.warnings || []).map((warn: string) => ({
              line: extractLineNumber(warn) || 1,
              message: warn,
              severity: "warning" as const,
            })),
          ];
          editorRef.value.setMarkers(markers);
        } else {
          editorRef.value?.clearMarkers();
        }
      } catch {
        codeErrors.value = ["验证请求失败"];
      } finally {
        validating.value = false;
      }
    }, 500);
  }
);

const extractLineNumber = (message: string): number | null => {
  const match = message.match(/line\s*(\d+)/i);
  return match ? parseInt(match[1]) : null;
};

const handleCursorChange = (position: { lineNumber: number; column: number }) => {
  cursorPosition.value = position;
};

const handleEditorReady = () => {};

const toggleConsole = () => {
  showConsole.value = !showConsole.value;
};

const loadDetail = async (id: string) => {
  try {
    const res = await strategyApi.getDetail(id);
    Object.assign(form, res.data);
    if (copyName) {
      form.name = copyName;
      form.id = "";
    }
  } catch {
    Message.error("加载策略失败");
  }
};

const loadTemplate = async (templateId: string) => {
  try {
    const res = await strategyApi.getTemplateDetail(templateId);
    form.code = res.data.code;
    form.name = "";
    form.parameters = res.data.params.reduce((acc, p) => {
      acc[p.name] = p.default;
      return acc;
    }, {} as Record<string, any>);
  } catch {
    Message.error("加载模板失败");
  }
};

onMounted(async () => {
  const strategyId = route.params.id as string;
  const templateId = route.query.templateId as string;

  if (strategyId) {
    await loadDetail(strategyId);
  } else if (copyFrom) {
    await loadDetail(copyFrom);
    if (copyName) form.name = copyName;
  } else if (templateId) {
    await loadTemplate(templateId);
  }
});

const handleSave = async () => {
  if (!form.name) return Message.warning("请输入策略名称");
  if (!form.code) return Message.warning("请输入策略代码");
  if (codeErrors.value.length > 0)
    return Message.warning("代码存在安全错误，请修复后保存");

  saving.value = true;
  try {
    const data: StrategyCreateRequest = {
      name: form.name,
      description: form.description,
      code: form.code,
      parameters: form.parameters,
      tag_ids: form.tags?.map((t) => (typeof t === "string" ? t : t.id)),
    };

    if (isEdit.value && !copyFrom) {
      await strategyApi.update(route.params.id as string, data);
    } else {
      const res = await strategyApi.create(data);
      if (res.data?.id) {
        router.replace({ name: "StrategyEditor", params: { id: res.data.id } });
      }
    }
    form.updated_at = new Date().toLocaleString();
    Message.success("保存成功");
  } catch {
    Message.error("保存失败");
  } finally {
    saving.value = false;
  }
};

const handleBack = () => {
  router.push({ name: "StrategyList" });
};

const handleRun = async () => {
  if (!form.code) return Message.warning("策略代码不能为空");
  if (codeErrors.value.length > 0)
    return Message.warning("代码存在安全错误，请修复后运行");

  running.value = true;
  logs.value = "";
  showConsole.value = true;

  try {
    let strategyId = form.id;
    if (!strategyId) {
      const res = await strategyApi.create({
        name: form.name || "未命名策略",
        code: form.code,
        parameters: form.parameters,
      });
      strategyId = res.data.id;
      form.id = strategyId;
    }

    const res = await strategyApi.startBacktest(strategyId, {
      strategy_id: strategyId,
      name: `${form.name}_回测`,
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      initial_capital: 100000,
    });
    logs.value = res.data || "回测已启动";
    Message.success("回测完成");
  } catch (err: any) {
    logs.value = `[ERROR] 执行出错: ${err?.message || err}`;
    Message.error("运行出错");
  } finally {
    running.value = false;
  }
};
</script>
