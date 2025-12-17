import type {
  PageParams,
  PageResult,
  SyncLog,
  SyncSummary,
  SyncTriggerParams
} from '@/types/api'
import { http } from './request'

export const syncApi = {
  summary: () => http.get<SyncSummary>('/v1/sync/summary'),
  logs: (params: PageParams) =>
    http.get<PageResult<SyncLog>>('/v1/sync/logs', params),
  trigger: (data: SyncTriggerParams) => http.post('/v1/sync/trigger', data)
}
