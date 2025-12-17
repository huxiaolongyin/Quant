// 统一响应结构
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
