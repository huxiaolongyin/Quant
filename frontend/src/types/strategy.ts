export type StrategyStatus = 'draft' | 'ready' | 'running' | 'paused' | 'archived'

export interface StrategyTag {
  id: string
  name: string
  color: string
  description?: string
}

export interface StrategyListItem {
  id: string
  name: string
  description?: string
  status: StrategyStatus
  returns: number
  win_rate: number
  tags: string[]
  updated_at: string
}

export interface StrategyDetail {
  id: string
  name: string
  description?: string
  code: string
  status: StrategyStatus
  is_active: boolean
  parameters: Record<string, any>
  max_position_size?: number
  stop_loss_ratio?: number
  take_profit_ratio?: number
  created_by?: string
  tags: StrategyTag[]
  created_at: string
  updated_at: string
}

export interface StrategyCreateRequest {
  name: string
  description?: string
  code: string
  parameters?: Record<string, any>
  max_position_size?: number
  stop_loss_ratio?: number
  take_profit_ratio?: number
  tag_ids?: string[]
}

export interface StrategyUpdateRequest {
  name?: string
  description?: string
  code?: string
  status?: StrategyStatus
  parameters?: Record<string, any>
  max_position_size?: number
  stop_loss_ratio?: number
  take_profit_ratio?: number
  tag_ids?: string[]
}

export interface StrategyListParams {
  page?: number
  page_size?: number
  search?: string
  status?: StrategyStatus
  tag_id?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface StrategyParamDef {
  name: string
  display_name: string
  type: 'int' | 'float' | 'str' | 'bool'
  default: any
  min?: number
  max?: number
  description?: string
}

export interface StrategyTemplate {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  params: StrategyParamDef[]
  is_builtin: boolean
}

export interface StrategyTemplateDetail extends StrategyTemplate {
  code: string
}

export interface CreateFromTemplateRequest {
  template_id: string
  name: string
  description?: string
  params?: Record<string, any>
  tag_ids?: string[]
}

export interface CodeValidateResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

export interface BacktestCreateRequest {
  strategy_id: string
  name: string
  start_date: string
  end_date: string
  initial_capital: number
}

export interface TagCreateRequest {
  name: string
  color?: string
  description?: string
}

export const STRATEGY_CATEGORY_MAP: Record<string, string> = {
  trend: '趋势跟踪',
  mean_reversion: '均值回归',
  momentum: '动量策略',
  volume: '量价策略',
  arbitrage: '套利策略'
}

export const STRATEGY_STATUS_MAP: Record<StrategyStatus, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'gray' },
  ready: { label: '就绪', color: 'blue' },
  running: { label: '运行中', color: 'green' },
  paused: { label: '已暂停', color: 'orange' },
  archived: { label: '已归档', color: 'gray' }
}