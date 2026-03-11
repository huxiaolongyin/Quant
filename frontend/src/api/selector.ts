import { http } from './request'

export interface ConditionNode {
  id?: number
  nodeType: 'group' | 'condition'
  logic?: 'and' | 'or'
  field?: string
  operator?: string
  value?: unknown
  children?: ConditionNode[]
}

export interface Selector {
  id: number
  name: string
  description?: string
  isActive: boolean
  rule: ConditionNode
  createdAt: string
  updatedAt: string
}

export interface SelectorListItem {
  id: number
  name: string
  description?: string
  isActive: boolean
  resultCount: number
  lastResultDate?: string
  lastResultCount?: number
  createdAt: string
  updatedAt: string
}

export interface SelectorField {
  id: number
  name: string
  label: string
  fieldType: 'basic' | 'quote' | 'indicator'
  dataType: 'string' | 'number' | 'date' | 'boolean'
  operators: string[]
  options?: { label: string; value: string }[]
  unit?: string
  description?: string
}

export interface FieldOption {
  label: string
  value: string
}

export interface SelectorResult {
  id: number
  selectorId: number
  tradeDate: string
  stockCodes: string[]
  count: number
  executionTime?: number
  createdAt: string
  stocks?: { full_stock_code: string; short_name: string; industry?: string }[]
}

export interface ExecuteResult {
  selectorId: number
  tradeDate: string
  stockCodes: string[]
  count: number
  executionTime: number
  stocks?: { full_stock_code: string; short_name: string; industry?: string }[]
}

const PREFIX = '/v1/selector'

export const selectorApi = {
  /**
   * 获取选股器列表
   */
  getList: (params?: {
    page?: number
    pageSize?: number
    name?: string
    isActive?: boolean
  }) => http.get<{ list: SelectorListItem[]; total: number }>(PREFIX, params),

  /**
   * 获取选股器详情
   */
  getById: (id: number) => http.get<Selector>(`${PREFIX}/${id}`),

  /**
   * 获取选股字段
   */
  getFields: () => http.get<SelectorField[]>(`${PREFIX}/fields`),

  /**
   * 创建选股器
   */
  create: (data: { name: string; description?: string; rule: ConditionNode }) =>
    http.post<Selector>(PREFIX, data),

  /**
   * 更新选股器
   */
  update: (
    id: number,
    data: {
      name?: string
      description?: string
      isActive?: boolean
      rule?: ConditionNode
    }
  ) => http.put<Selector>(`${PREFIX}/${id}`, data),

  /**
   * 删除选股器
   */
  delete: (id: number) => http.delete(`${PREFIX}/${id}`),

  /**
   * 执行选股
   */
  execute: (id: number, tradeDate?: string) =>
    http.post<ExecuteResult>(`${PREFIX}/${id}/execute`, undefined, {
      params: tradeDate ? { trade_date: tradeDate } : undefined
    }),

/**
   * 获取执行结果
   */
  getResults: (id: number, params?: { page?: number; pageSize?: number }) =>
    http.get<{ list: SelectorResult[]; total: number }>(
      `${PREFIX}/${id}/results`,
      params
    ),

  /**
   * 获取单次选股结果详情
   */
  getResultById: (selectorId: number, resultId: number) =>
    http.get<SelectorResult>(`${PREFIX}/${selectorId}/results/${resultId}`),

  /**
   * 获取字段选项(行业/省份/城市)
   */
  getOptions: (field: 'industry' | 'province' | 'city', province?: string) =>
    http.get<FieldOption[]>(`${PREFIX}/options`, { field, province }),
}
