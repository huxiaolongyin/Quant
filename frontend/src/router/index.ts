import AppLayout from '@/components/Layout/AppLayout.vue'
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const Dashboard = () => import('@/views/Dashboard.vue')
const Watchlist = () => import('@/views/Market/Watchlist.vue')
const DataSync = () => import('@/views/Data/SyncManager.vue')
const SelectorList = () => import('@/views/Selector/List.vue')
const SelectorEditor = () => import('@/views/Selector/Editor.vue')
const StrategyList = () => import('@/views/Strategy/List.vue')
const StrategyEditor = () => import('@/views/Strategy/Editor.vue')
const StrategyTemplates = () => import('@/views/Strategy/Templates.vue')
const StrategyCreateFromTemplate = () => import('@/views/Strategy/CreateFromTemplate.vue')
const BacktestReport = () => import('@/views/Strategy/BacktestReport.vue')
const Settings = () => import('@/views/Settings/Index.vue')
const Login = () => import('@/views/Auth/Login.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
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
        path: 'selector/list',
        name: 'SelectorList',
        component: SelectorList,
        meta: { title: '选股器' }
      },
      {
        path: 'selector/editor/:id?',
        name: 'SelectorEditor',
        component: SelectorEditor,
        meta: { title: '选股器编辑' }
      },
      {
        path: 'strategy/list',
        name: 'StrategyList',
        component: StrategyList,
        meta: { title: '策略工场' }
      },
      {
        path: 'strategy/templates',
        name: 'StrategyTemplates',
        component: StrategyTemplates,
        meta: { title: '选择策略模板' }
      },
      {
        path: 'strategy/create/:templateId',
        name: 'StrategyCreateFromTemplate',
        component: StrategyCreateFromTemplate,
        meta: { title: '创建策略' }
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
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings,
        meta: { title: '设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token || localStorage.getItem('token')

  if (to.meta.requiresAuth !== false) {
    if (!token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    if (!userStore.userInfo) {
      const success = await userStore.fetchUserInfo()
      if (!success) {
        next({ name: 'Login' })
        return
      }
    }

    if (to.meta.permission && !userStore.hasPermission(to.meta.permission as string)) {
      next({ name: 'Dashboard' })
      return
    }

    if (to.name === 'Settings' && !userStore.hasPermission('user') && !userStore.hasPermission('role')) {
      next({ name: 'Dashboard' })
      return
    }
  }

  if (to.name === 'Login' && token && userStore.userInfo) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router