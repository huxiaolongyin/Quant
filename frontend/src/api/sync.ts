import type {
  PageParams,
  PageResult,
  SyncLog,
  SyncSummary,
  SyncTriggerParams,
  SchedulerUpdateParams
} from '@/types/api'
import { http } from './request'

export const syncApi = {
  summary: () => http.get<SyncSummary>('/v1/sync/summary'),
  logs: (params: PageParams) =>
    http.get<PageResult<SyncLog>>('/v1/sync/logs', params),
  trigger: (data: SyncTriggerParams) => http.post('/v1/sync/trigger', data),
  updateScheduler: (data: SchedulerUpdateParams) =>
    http.put('/v1/sync/scheduler', data)
}
