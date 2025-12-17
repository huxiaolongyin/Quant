// 定义策略数据接口
export interface Strategy {
  id: string
  name: string
  code: string
  description?: string
  updatedAt?: string
}

// 模拟的 Python 策略模板
const DEFAULT_CODE = `# 导入函数库
import jqdata

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 设定成交量比例
    set_option('order_volume_ratio', 1)
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    g.security = '000001.XSHE'

def handle_data(context, data):
    order(g.security, 100)
`

export interface StrategyItem {
  id: string
  name: string
  description: string
  status: 'running' | 'stopped' | 'backtesting'
  tags: string[]
  returns: number // 累计收益率
  winRate: number // 胜率
  updatedAt: string
}

// 模拟获取策略列表
export const fetchGetStrategyList = (): Promise<StrategyItem[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      // 生成8个模拟数据
      const list: StrategyItem[] = Array.from({ length: 8 }).map(
        (_, index) => ({
          id: String(index + 1),
          name: index === 0 ? '双均线策略_Demo' : `多因子选股策略 v${index}.0`,
          description:
            index % 2 === 0
              ? '基于MA5和MA20的金叉死叉交易策略'
              : '基于市值、PE、ROE等多因子打分的选股模型',
          status: index === 0 ? 'running' : 'stopped',
          tags: index % 2 === 0 ? ['趋势', '均线'] : ['选股', '多因子'],
          returns: Number((Math.random() * 50 - 10).toFixed(2)),
          winRate: Number((Math.random() * 100).toFixed(0)),
          updatedAt: '2023-10-27 14:30'
        })
      )
      resolve(list)
    }, 600)
  })
}

// 模拟获取策略详情
export const fetchStrategyDetail = (id: string): Promise<Strategy> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        id,
        name: '双均线策略_Demo',
        code: DEFAULT_CODE,
        description: '这是一个简单的测试策略',
        updatedAt: new Date().toLocaleString()
      })
    }, 500)
  })
}

// 模拟保存策略
export const fetchSaveStrategy = (strategy: Strategy): Promise<boolean> => {
  return new Promise(resolve => {
    setTimeout(() => {
      console.log('Strategy Saved:', strategy)
      resolve(true)
    }, 800)
  })
}

// 模拟运行回测
export const fetchRunStrategyBacktest = (code: string): Promise<string> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(`[INFO] 2023-01-01 09:30:00 - INFO - 策略启动
[INFO] 2023-01-01 09:30:00 - INFO - 运行初始化函数
[INFO] 2023-01-02 09:30:00 - INFO - 买入 000001.XSHE 100股
[INFO] 2023-01-02 15:00:00 - INFO - 回测完成，收益率: 12.5%
`)
    }, 1500)
  })
}
