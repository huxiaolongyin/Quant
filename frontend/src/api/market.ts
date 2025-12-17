import type {
  HistoryQuotesParams,
  KlineData,
  PageParams,
  PageResult,
  RealtimeQuote,
  WatchlistStock,
  WatchlistStockCreate,
  WatchlistStockReorder,
  WatchlistStockUpdate
} from '@/types/api'
import { http } from './request'

const PREFIX = '/v1/watchlist'

export const marketApi = {
  /**
   * 获取自选股票列表
   */
  getList: (params?: PageParams) =>
    http.get<PageResult<WatchlistStock>>(PREFIX, params),

  /**
   * 获取自选股票详情
   */
  getById: (id: number) => http.get<WatchlistStock>(`${PREFIX}/${id}`),

  /**
   * 添加自选股票
   */
  create: (data: WatchlistStockCreate) =>
    http.post<WatchlistStock>(PREFIX, data),

  /**
   * 更新自选股票
   */
  update: (id: number, data: WatchlistStockUpdate) =>
    http.put<WatchlistStock>(`${PREFIX}/${id}`, data),

  /**
   * 删除自选股票
   */
  delete: (id: number) => http.delete(`${PREFIX}/${id}`),

  /**
   * 调整排序
   */
  reorder: (data: WatchlistStockReorder) =>
    http.post<{ updated: number }>(`${PREFIX}/reorder`, data),

  /**
   * 获取实时行情列表
   */
  getRealtime: () => http.get<RealtimeQuote[]>(`${PREFIX}/realtime`),

  /**
   * 获取单只股票历史行情
   */
  getHistory: (id: number, params?: HistoryQuotesParams) =>
    http.get<KlineData[]>(`${PREFIX}/${id}/history`, params)
}
