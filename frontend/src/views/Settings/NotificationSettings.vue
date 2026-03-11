<template>
  <div class="py-2 px-6 space-y-6">
    <div class="flex justify-between items-center">
      <div class="text-gray-500 text-sm">
        配置消息通知渠道，支持钉钉、企业微信、飞书机器人
      </div>
      <a-button type="primary" @click="openModal()">
        <template #icon><icon-plus /></template>
        新增渠道
      </a-button>
    </div>

    <a-card :bordered="false" class="shadow-sm rounded-lg">
      <a-table :data="channels" :loading="loading" :pagination="false">
        <template #columns>
          <a-table-column title="渠道名称" data-index="name" :width="150" />
          <a-table-column title="类型" data-index="channelType" :width="120">
            <template #cell="{ record }">
              <a-tag :color="getChannelColor(record.channelType)">
                {{ getChannelLabel(record.channelType) }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="Webhook" :width="300">
            <template #cell="{ record }">
              <span class="text-gray-500 text-xs truncate block max-w-xs">
                {{ maskWebhook(record.webhookUrl) }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <a-switch
                :model-value="record.isEnabled"
                size="small"
                @change="(val) => handleToggle(record.id, val as boolean)"
              />
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="180">
            <template #cell="{ record }">
              <a-space>
                <a-button
                  size="small"
                  @click="handleTest(record.id)"
                  :loading="record.testing"
                >
                  测试
                </a-button>
                <a-button size="small" @click="openModal(record)">编辑</a-button>
                <a-popconfirm
                  content="确定删除此通知渠道？"
                  @ok="handleDelete(record.id)"
                >
                  <a-button size="small" status="danger">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:visible="modalVisible"
      :title="isEdit ? '编辑渠道' : '新增渠道'"
      @ok="handleSubmit"
      @cancel="resetForm"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item label="渠道名称" required>
          <a-input v-model="formData.name" placeholder="如：交易信号通知" />
        </a-form-item>
        <a-form-item label="渠道类型" required>
          <a-select v-model="formData.channelType" :disabled="isEdit">
            <a-option
              v-for="item in CHANNEL_TYPE_OPTIONS"
              :key="item.value"
              :value="item.value"
            >
              {{ item.label }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Webhook URL" required>
          <a-input v-model="formData.webhookUrl" placeholder="输入机器人 Webhook 地址" />
        </a-form-item>
        <a-form-item v-if="formData.channelType !== 'wechat'" label="签名密钥">
          <a-input-password v-model="formData.secret" placeholder="可选，用于签名验证" />
          <template #extra>
            <span class="text-xs text-gray-400"
              >钉钉/飞书机器人的加签密钥，提高安全性</span
            >
          </template>
        </a-form-item>
        <a-form-item label="是否启用">
          <a-switch v-model="formData.isEnabled" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-card title="发送测试消息" :bordered="false" class="shadow-sm rounded-lg">
      <div class="space-y-4">
        <a-form :model="testMessage" layout="inline">
          <a-form-item label="消息标题">
            <a-input
              v-model="testMessage.title"
              placeholder="测试通知"
              style="width: 200px"
            />
          </a-form-item>
          <a-form-item label="消息内容">
            <a-input
              v-model="testMessage.content"
              placeholder="这是一条测试消息"
              style="width: 300px"
            />
          </a-form-item>
          <a-form-item label="Markdown">
            <a-switch v-model="testMessage.isMarkdown" size="small" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="handleSendTest" :loading="sending">
              发送测试
            </a-button>
          </a-form-item>
        </a-form>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import {
  createChannel,
  deleteChannel,
  getChannels,
  sendNotification,
  testChannel,
  toggleChannel,
  updateChannel,
} from "@/api/notification";
import type {
  ChannelType,
  NotificationChannel,
  NotificationChannelCreate,
} from "@/types/notification";
import { CHANNEL_TYPE_OPTIONS } from "@/types/notification";
import { Message } from "@arco-design/web-vue";
import { IconPlus } from "@arco-design/web-vue/es/icon";
import { onMounted, reactive, ref } from "vue";

const loading = ref(false);
const channels = ref<(NotificationChannel & { testing?: boolean })[]>([]);
const modalVisible = ref(false);
const isEdit = ref(false);
const editingId = ref<number | null>(null);
const sending = ref(false);

const formData = reactive<NotificationChannelCreate>({
  name: "",
  channelType: "dingtalk",
  webhookUrl: "",
  secret: "",
  isEnabled: true,
});

const testMessage = reactive({
  title: "测试通知",
  content: "这是一条来自量化交易系统的测试消息",
  isMarkdown: false,
});

const getChannelLabel = (type: ChannelType) => {
  return CHANNEL_TYPE_OPTIONS.find((o) => o.value === type)?.label || type;
};

const getChannelColor = (type: ChannelType) => {
  const colors: Record<ChannelType, string> = {
    dingtalk: "blue",
    wechat: "green",
    feishu: "purple",
  };
  return colors[type] || "gray";
};

const maskWebhook = (url: string) => {
  if (!url) return "";
  try {
    const u = new URL(url);
    return `${u.protocol}//${u.host}/***(已隐藏)`;
  } catch {
    return url.substring(0, 30) + "...";
  }
};

const loadChannels = async () => {
  loading.value = true;
  try {
    const res = await getChannels();
    channels.value = res.data || [];
  } catch (e) {
    Message.error("加载渠道列表失败");
  } finally {
    loading.value = false;
  }
};

const openModal = (channel?: NotificationChannel) => {
  if (channel) {
    isEdit.value = true;
    editingId.value = channel.id;
    formData.name = channel.name;
    formData.channelType = channel.channelType;
    formData.webhookUrl = channel.webhookUrl;
    formData.secret = channel.secret || "";
    formData.isEnabled = channel.isEnabled;
  } else {
    isEdit.value = false;
    editingId.value = null;
    resetForm();
  }
  modalVisible.value = true;
};

const resetForm = () => {
  formData.name = "";
  formData.channelType = "dingtalk";
  formData.webhookUrl = "";
  formData.secret = "";
  formData.isEnabled = true;
};

const handleSubmit = async () => {
  if (!formData.name || !formData.webhookUrl) {
    Message.warning("请填写必填项");
    return false;
  }

  try {
    if (isEdit.value && editingId.value) {
      await updateChannel(editingId.value, formData);
      Message.success("更新成功");
    } else {
      await createChannel(formData);
      Message.success("创建成功");
    }
    modalVisible.value = false;
    loadChannels();
    return true;
  } catch (e) {
    Message.error("操作失败");
    return false;
  }
};

const handleToggle = async (id: number, enabled: boolean) => {
  try {
    await toggleChannel(id, enabled);
    const channel = channels.value.find((c) => c.id === id);
    if (channel) channel.isEnabled = enabled;
    Message.success(enabled ? "已启用" : "已禁用");
  } catch (e) {
    Message.error("操作失败");
  }
};

const handleDelete = async (id: number) => {
  try {
    await deleteChannel(id);
    Message.success("删除成功");
    loadChannels();
  } catch (e) {
    Message.error("删除失败");
  }
};

const handleTest = async (id: number) => {
  const channel = channels.value.find((c) => c.id === id);
  if (!channel) return;

  channel.testing = true;
  try {
    const res = await testChannel(id);
    if (res.data?.success) {
      Message.success("测试消息发送成功");
    } else {
      Message.error(res.data?.message || "测试失败");
    }
  } catch (e) {
    Message.error("测试失败");
  } finally {
    channel.testing = false;
  }
};

const handleSendTest = async () => {
  sending.value = true;
  try {
    const res = await sendNotification(testMessage);
    if (res.data?.success > 0) {
      Message.success(`成功发送 ${res.data.success}/${res.data.total} 个渠道`);
      if (res.data.failed > 0) {
        Message.warning(`${res.data.failed} 个渠道发送失败`);
      }
    } else {
      Message.error("发送失败");
    }
  } catch (e) {
    Message.error("发送失败");
  } finally {
    sending.value = false;
  }
};

onMounted(() => {
  loadChannels();
});
</script>
