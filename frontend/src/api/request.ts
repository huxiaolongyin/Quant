import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig
} from 'axios'
import type { ApiResponse, RequestConfig } from './types'

// 扩展 AxiosRequestConfig
declare module 'axios' {
  interface AxiosRequestConfig extends RequestConfig {}
}

class Request {
  private instance: AxiosInstance

  constructor () {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL,
      timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors () {
    // 请求拦截
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      error => Promise.reject(error)
    )

    // 响应拦截
    this.instance.interceptors.response.use(
      response => {
        const { data, config } = response

        // 业务错误处理
        if (data.code !== 0 && data.code !== 200) {
          // 默认显示错误，除非明确关闭
          if (config.showError !== false) {
            // 这里可以用 ElMessage、Toast 等
            console.error(data.message || '请求失败')
          }

          // 如果需要自己处理错误，返回完整响应
          if (config.handleError) {
            return Promise.reject(data)
          }
        }

        return data
      },
      error => {
        // HTTP 错误处理
        const status = error.response?.status
        const messages: Record<number, string> = {
          401: '登录已过期',
          403: '没有权限',
          404: '资源不存在',
          500: '服务器错误'
        }

        console.error(messages[status] || error.message)

        // 401 跳转登录
        if (status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }

        return Promise.reject(error)
      }
    )
  }

  // 泛型请求方法
  request<T> (config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.request(config)
  }

  get<T> (
    url: string,
    params?: object,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.instance.get(url, { params, ...config })
  }

  post<T> (
    url: string,
    data?: object,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.instance.post(url, data, config)
  }

  put<T> (
    url: string,
    data?: object,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.instance.put(url, data, config)
  }

  delete<T> (url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.instance.delete(url, config)
  }
}

export const http = new Request()
