<template>
  <div class="h-full flex flex-col bg-slate-100 dark:bg-slate-950">
    <header class="card border-b px-4 h-14 flex justify-between items-center z-10">
      <div class="flex items-center gap-4">
        <a-button type="text" shape="circle" @click="handleBack">
          <template #icon><span class="material-symbols-outlined">arrow_back</span></template>
        </a-button>

        <div class="flex flex-col">
          <a-input
            v-model="form.name"
            placeholder="请输入策略名称"
            class="!bg-transparent !border-none !px-0 !h-auto text-lg font-bold text-slate-800 dark:text-white focus:!bg-slate-100 dark:focus:!bg-slate-800"
          />
          <span class="text-xs text-slate-400" v-if="form.updatedAt">上次保存: {{ form.updatedAt }}</span>
        </div>
      </div>

      <a-space>
        <a-button @click="handleSave" :loading="saving">
          <template #icon><span class="material-symbols-outlined text-base">save</span></template>
          保存
        </a-button>
        <a-button type="primary" status="success" @click="handleRun" :loading="running">
          <template #icon><span class="material-symbols-outlined text-base">play_arrow</span></template>
          运行回测
        </a-button>
      </a-space>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 flex flex-col border-r border-slate-200 dark:border-slate-700 relative">
        <div class="card border-b px-4 py-1 text-xs text-muted flex justify-between">
          <span>Python 3.8</span>
          <span>main.py</span>
        </div>
        <textarea
          v-model="form.code"
          class="flex-1 w-full h-full resize-none bg-[#1e1e1e] text-gray-300 p-4 font-mono text-sm outline-none leading-6"
          spellcheck="false"
        ></textarea>
      </div>

      <div class="w-[400px] card flex flex-col transition-all duration-300" :class="{ '!w-0': !showConsole }">
        <div class="h-9 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-4 bg-slate-50 dark:bg-slate-950">
          <span class="font-bold text-slate-700 dark:text-slate-200">控制台输出</span>
          <a-button type="text" size="mini" @click="logs = ''">清空</a-button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 bg-[#2b2b2b] font-mono text-xs">
          <div v-if="!logs && !running" class="text-gray-500 text-center mt-10">暂无运行日志</div>
          <div v-else class="whitespace-pre-wrap text-green-400">{{ logs }}</div>
          <div v-if="running" class="mt-2 text-blue-400 animate-pulse">> 正在执行策略回测...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchRunStrategyBacktest, fetchSaveStrategy, fetchStrategyDetail, type Strategy } from '@/api/strategy';
import { Message } from '@arco-design/web-vue';
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const saving = ref(false);
const running = ref(false);
const showConsole = ref(true);
const logs = ref('');

const form = reactive<Strategy>({
  id: '',
  name: '',
  code: '',
  updatedAt: ''
});

onMounted(async () => {
  const strategyId = '1';
  try {
    const data = await fetchStrategyDetail(strategyId);
    Object.assign(form, data);
  } catch (err) {
    Message.error('加载策略失败');
  }
});

const handleSave = async () => {
  if (!form.name) return Message.warning('请输入策略名称');

  saving.value = true;
  try {
    await fetchSaveStrategy(form);
    form.updatedAt = new Date().toLocaleString();
    Message.success('保存成功');
  } catch (err) {
    Message.error('保存失败');
  } finally {
    saving.value = false;
  }
};

const handleBack = () => {
  router.push({ name: 'StrategyList' });
};

const handleRun = async () => {
  if (!form.code) return Message.warning('策略代码不能为空');

  running.value = true;
  logs.value = '';
  showConsole.value = true;

  try {
    const result = await fetchRunStrategyBacktest(form.code);
    logs.value = result;
    Message.success('回测完成');
  } catch (err) {
    logs.value = `[ERROR] 执行出错: ${err}`;
    Message.error('运行出错');
  } finally {
    running.value = false;
  }
};
</script>