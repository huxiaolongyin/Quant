import AppLayout from '@/components/Layout/AppLayout.vue'
import { createRouter, createWebHistory } from 'vue-router'

// 使用懒加载
const Dashboard = () => import('@/views/Dashboard.vue')
const Watchlist = () => import('@/views/Market/Watchlist.vue')
const DataSync = () => import('@/views/Data/SyncManager.vue')
const StrategyList = () => import('@/views/Strategy/List.vue')
const StrategyEditor = () => import('@/views/Strategy/Editor.vue')
const BacktestReport = () => import('@/views/Strategy/BacktestReport.vue')

const routes = [
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘' }
      },
      {
        path: 'market/watchlist',
        name: 'Watchlist',
        component: Watchlist,
        meta: { title: '自选股行情' }
      },
      {
        path: 'data/sync',
        name: 'DataSync',
        component: DataSync,
        meta: { title: '数据同步管理' }
      },
      {
        path: 'strategy/list',
        name: 'StrategyList',
        component: StrategyList,
        meta: { title: '策略工场' }
      },
      {
        path: 'strategy/editor/:id?',
        name: 'StrategyEditor',
        component: StrategyEditor,
        meta: { title: '策略代码编辑器' }
      },
      {
        path: 'strategy/backtest',
        name: 'BacktestReport',
        component: BacktestReport,
        meta: { title: '回测绩效分析' }
      }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
