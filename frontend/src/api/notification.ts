import type {
  NotificationChannel,
  NotificationChannelCreate,
  NotificationChannelUpdate,
  NotificationSend,
  NotificationTestResult
} from '@/types/notification'
import { http } from './request'
import type { ApiResponse } from './types'

export function getChannels (): Promise<ApiResponse<NotificationChannel[]>> {
  return http.get('/v1/notification/channels')
}

export function createChannel (
  data: NotificationChannelCreate
): Promise<ApiResponse<NotificationChannel>> {
  return http.post('/v1/notification/channels', data)
}

export function updateChannel (
  id: number,
  data: NotificationChannelUpdate
): Promise<ApiResponse<NotificationChannel>> {
  return http.put(`/v1/notification/channels/${id}`, data)
}

export function deleteChannel (id: number): Promise<ApiResponse<void>> {
  return http.delete(`/v1/notification/channels/${id}`)
}

export function toggleChannel (
  id: number,
  isEnabled: boolean
): Promise<ApiResponse<NotificationChannel>> {
  return http.post(`/v1/notification/channels/${id}/toggle`, undefined, {
    params: { is_enabled: isEnabled }
  })
}

export function testChannel (
  id: number
): Promise<ApiResponse<NotificationTestResult>> {
  return http.post(`/v1/notification/channels/${id}/test`)
}

export function sendNotification (data: NotificationSend): Promise<
  ApiResponse<{
    total: number
    success: number
    failed: number
    errors: string[]
  }>
> {
  return http.post('/v1/notification/send', data)
}
