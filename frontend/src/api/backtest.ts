// 定义回测配置参数接口
export interface BacktestConfig {
  strategyId: string
  codes: string[] // 支持多只股票
  dateRange: string[] // [startDate, endDate]
  initialCapital: number
  frequency: '1d' | '1h' | '30m' | '15m' | '5m' | '1m'
}

// 定义回测结果接口
export interface BacktestResult {
  summary: {
    totalReturns: number // 总收益率
    annualizedReturns: number // 年化收益
    maxDrawdown: number // 最大回撤
    sharpeRatio: number // 夏普比率
    alpha: number
    beta: number
  }
  info: {
    strategyName: string
    period: string
  }
  // 模拟图表数据
  charts: {
    dates: string[]
    strategyValues: number[]
    benchmarkValues: number[]
  }
}

// 模拟策略列表
const MOCK_STRATEGIES = [
  { id: 's1', name: '双均线策略_V2 (Double MA)' },
  { id: 's2', name: '海龟交易法则 (Turtle Trading)' },
  { id: 's3', name: '多因子选股 (Multi-Factor)' },
  { id: 's4', name: 'RSI均值回归 (RSI Reversion)' }
]

// 模拟股票搜索数据
const MOCK_STOCKS = [
  { value: '000001.SZ', label: '平安银行' },
  { value: '600519.SH', label: '贵州茅台' },
  { value: '300750.SZ', label: '宁德时代' },
  { value: '000858.SZ', label: '五粮液' },
  { value: '601988.SH', label: '中国银行' }
]

// 1. 获取可用策略列表
export const fetchStrategies = async () => {
  return new Promise<{ id: string; name: string }[]>(resolve => {
    setTimeout(() => resolve(MOCK_STRATEGIES), 500)
  })
}

// 2. 搜索股票 (模拟)
export const fetchSearchStocks = async (query: string) => {
  return new Promise<{ value: string; label: string }[]>(resolve => {
    setTimeout(() => {
      if (!query) resolve(MOCK_STOCKS)
      else
        resolve(
          MOCK_STOCKS.filter(
            s => s.label.includes(query) || s.value.includes(query)
          )
        )
    }, 300)
  })
}

// 3. 执行回测 (核心接口)
export const fetchRunBacktest = async (config: BacktestConfig) => {
  console.log('提交回测配置:', config)

  return new Promise<BacktestResult>(resolve => {
    setTimeout(() => {
      // 模拟生成随机回测数据
      const isWin = Math.random() > 0.3
      resolve({
        summary: {
          totalReturns: isWin ? 42.8 : -15.2,
          annualizedReturns: isWin ? 18.5 : -8.4,
          maxDrawdown: isWin ? -12.3 : -25.6,
          sharpeRatio: isWin ? 1.45 : -0.2,
          alpha: 0.05,
          beta: 0.92
        },
        info: {
          strategyName:
            MOCK_STRATEGIES.find(s => s.id === config.strategyId)?.name ||
            '未知策略',
          period: `${config.dateRange[0]} 至 ${config.dateRange[1]}`
        },
        charts: {
          dates: ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05'],
          strategyValues: [1.0, 1.1, 1.05, 1.2, 1.42],
          benchmarkValues: [1.0, 1.02, 0.98, 1.05, 1.1]
        }
      })
    }, 1500) // 模拟计算耗时
  })
}
