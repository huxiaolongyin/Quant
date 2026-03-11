export type ChannelType = 'dingtalk' | 'wechat' | 'feishu'

export interface NotificationChannel {
  id: number
  name: string
  channelType: ChannelType
  webhookUrl: string
  secret?: string
  isEnabled: boolean
  createdAt: string
  updatedAt: string
}

export interface NotificationChannelCreate {
  name: string
  channelType: ChannelType
  webhookUrl: string
  secret?: string
  isEnabled?: boolean
}

export interface NotificationChannelUpdate {
  name?: string
  webhookUrl?: string
  secret?: string
  isEnabled?: boolean
}

export interface NotificationSend {
  channels?: number[]
  title: string
  content: string
  isMarkdown?: boolean
}

export interface NotificationTestResult {
  success: boolean
  message: string
}

export const CHANNEL_TYPE_OPTIONS = [
  { label: '钉钉机器人', value: 'dingtalk' },
  { label: '企业微信机器人', value: 'wechat' },
  { label: '飞书机器人', value: 'feishu' }
] as const