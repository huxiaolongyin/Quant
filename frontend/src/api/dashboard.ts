
import { http } from './request'
import { Overview } from '@/types/api'
const PREFIX = '/v1/overview'

export const dashboardApi = {
    /**
     * 获取总览指标
     */
    getOverview: () => http.get<Overview>(PREFIX)
}
