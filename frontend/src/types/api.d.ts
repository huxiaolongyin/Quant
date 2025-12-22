import { SyncType } from 'enums'
// =====================================================================
//                           基础
// =====================================================================

export interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

// 分页请求
export interface PageParams {
  page: number
  pageSize: number
}

// 分页响应
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

// =====================================================================
//                           总览
// =====================================================================
export type Overview = {
  totalMarketValue: number
  dailyReturn: number
  dailyReturnRate: number
}

// =====================================================================
//                           数据同步
// =====================================================================
export interface SyncScheduler {
  enabled: boolean
  time: string
}

export interface SyncSummary {
  lastSyncTime: number
  dataRange: string
  statDays: number
  stockCount: number
  scheduler: SyncScheduler
  status: 'idle' | 'running' | 'error'
}

export interface SyncLog {
  id: string
  type: SyncType
  range: string
  startTime: string
  duration: string
  status: 'success' | 'fail' | 'running'
}

// 请求配置扩展
export interface RequestConfig {
  /** 是否显示 loading */
  loading?: boolean
  /** 是否显示错误提示 */
  showError?: boolean
  /** 自定义错误处理 */
  handleError?: boolean
}

export interface SyncTriggerParams {
  type: SyncType
  dataRange: str[]
  payload?: any
}

// =====================================================================
//                           自选股票
// =====================================================================

/** 自选股票 */
export interface WatchlistStock {
  id: number
  stockId: number
  holdingNum: number
  costPrice: number | string
  sortOrder: number
  notes?: string
  createdAt: string
  updatedAt: string
  stockCode: string
  shortName: string
}

/** 添加自选股票参数 */
export interface WatchlistStockCreate {
  stockId: number
  holdingNum?: number
  costPrice?: number | string
  sortOrder?: number
  notes?: string
}

/** 更新自选股票参数 */
export interface WatchlistStockUpdate {
  holdingNum?: number
  costPrice?: number | string
  sortOrder?: number
  notes?: string
}

/** 排序项 */
export interface ReorderItem {
  id: number
  sortOrder: number
}

/** 调整排序参数 */
export interface WatchlistStockReorder {
  items: ReorderItem[]
}

// =====================================================================
//                         历史行情
// =====================================================================

/** K线周期 */
export type KlinePeriod = 'daily' | 'weekly' | 'monthly'

/** 历史行情查询参数 */
export interface HistoryQuotesParams {
  period?: KlinePeriod
  startDate?: string
  endDate?: string
  limit?: number
}

/** K线数据 */
export interface KlineData {
  tradeDate: string
  open: number | string
  high: number | string
  low: number | string
  close: number | string
  volume: number
  turnover?: number | string
}

// K线图表数据格式（适配 ECharts）
export interface ChartKLineData {
  dates: string[]
  values: number[][] // [Open, Close, Low, High]
  volumes: number[]
}
// =====================================================================
//                         实时行情（预留）
// =====================================================================

export interface MinuteData {
  time: string
  open: number
  close: number
  hight: number
  low: number
  volume: number
}

/** 实时行情数据 */
export type RealtimeQuote = {
  code: string
  latestPrice: number
  preClose: number
  change: number
  changePercent: number
  open: number
  high: number
  low: number
  volume: number
  holdingNum: number
  marketValue: number
  preMarketValue: number
  bars: MinuteData[]
}
