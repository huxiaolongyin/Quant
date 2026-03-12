import type {
  BacktestCreateRequest,
  CodeValidateResult,
  CreateFromTemplateRequest,
  StrategyCreateRequest,
  StrategyDetail,
  StrategyListItem,
  StrategyListParams,
  StrategyTag,
  StrategyTemplate,
  StrategyTemplateDetail,
  StrategyUpdateRequest,
  TagCreateRequest
} from '@/types/strategy'
import { http } from './request'
import type { ApiResponse, PaginatedResponse } from './types'

const BASE_URL = '/v1/strategy'

export const strategyApi = {
  getTemplates (category?: string): Promise<ApiResponse<StrategyTemplate[]>> {
    return http.get(`${BASE_URL}/templates`, { category })
  },

  getTemplateDetail (id: string): Promise<ApiResponse<StrategyTemplateDetail>> {
    return http.get(`${BASE_URL}/templates/${id}`)
  },

  createFromTemplate (
    data: CreateFromTemplateRequest
  ): Promise<ApiResponse<StrategyDetail>> {
    return http.post(`${BASE_URL}/from-template`, data)
  },

  validateCode (code: string): Promise<CodeValidateResult> {
    return http.post(`${BASE_URL}/validate-code`, { code })
  },

  getList (
    params: StrategyListParams
  ): Promise<PaginatedResponse<StrategyListItem>> {
    return http.get(BASE_URL, params)
  },

  getDetail (id: string): Promise<ApiResponse<StrategyDetail>> {
    return http.get(`${BASE_URL}/${id}`)
  },

  create (data: StrategyCreateRequest): Promise<ApiResponse<StrategyDetail>> {
    return http.post(BASE_URL, data)
  },

  update (
    id: string,
    data: StrategyUpdateRequest
  ): Promise<ApiResponse<StrategyDetail>> {
    return http.put(`${BASE_URL}/${id}`, data)
  },

  delete (id: string): Promise<ApiResponse<null>> {
    return http.delete(`${BASE_URL}/${id}`)
  },

  startBacktest (
    id: string,
    data: BacktestCreateRequest
  ): Promise<ApiResponse<string>> {
    return http.post(`${BASE_URL}/${id}/backtest`, data)
  },

  getTags (): Promise<ApiResponse<StrategyTag[]>> {
    return http.get(`${BASE_URL}/tags`)
  },

  createTag (data: TagCreateRequest): Promise<ApiResponse<StrategyTag>> {
    return http.post(`${BASE_URL}/tags`, data)
  }
}
