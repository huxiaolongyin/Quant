# 量化股票系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Vue-3.x-green?logo=vue.js" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
  <img src="https://img.shields.io/badge/Status-开发中-orange" />
</p>

面向中国 A 股市场的**量化选股与回测系统**，提供可视化策略配置、智能选股、历史回测和多渠道信号推送。

核心逻辑：每日自动同步数据 → 进行基础配置(税率、通知方式等) → 添加选股策略 → 编辑策略(RSI、MACD 等) → 回测分析 → 出现交易信号时推送通知

## ✨ 功能概览

| 模块        | 描述                                   | 状态 |
| ----------- | -------------------------------------- | ---- |
| 📊 仪表盘   | 系统概览、持仓收益、策略运行状态       | 📋   |
| ⭐ 自选行情 | 关注股票的实时/历史行情展示            | ✅   |
| 🔄 数据同步 | 支持自动/手动/补数同步每日行情数据     | ✅   |
| 🔍 选股器   | 可视化配置选股条件，筛选目标股票池     | 📋   |
| 🏭 策略工厂 | 内置 RSI、MACD、均线等策略，支持自定义 | 📋   |
| ⚙️ 参数调优 | 基于 Optuna 的策略参数自动优化         | 📋   |
| 📈 回测分析 | 策略回测、收益曲线、交易明细报告       | 📋   |
| 🔔 信号通知 | 邮件/企业微信/钉钉 推送交易信号        | 📋   |
| ⚡ 基础配置 | 税率、手续费、通知渠道等系统设置       | 📋   |

> ✅ 已完成 | 🚧 开发中 | 📋 计划中

## 📸 界面预览

TODO: 待添加

## 🔍 选股器

筛选过滤股票列表，用于跑策略和股票查看

- 版本管理
- json 的过滤
  - 简单过滤，对 stock 表字段进行过滤
  - 复杂过滤，对 DailyLine 配置具体指标计算方式(最新价、涨停次数)，对外只展示: 指标 比较符 value
- 缓存机制：每天计算一次即可

```yaml
选股条件:
  - 交易所: 深圳 # 经济特区，发展快
  - 排除: ST/*ST 股票 # 风险过高
  - 股价: <= 50 元 # 资金门槛考虑
  - 排除行业: 房地产, 建筑业 # 行业周期因素
  - 排除: 近 15 日内有数次涨停/跌停 # 波动过大，不易把控
```

## 📈 策略工厂

- 版本管理
- 代码安全
  - 防止代码注入，只允许白名单模块与固定的函数 template
  - 使用 RestrictedPython
- 可配参数，支持未来进行参数调优

| 策略名称   | 类型 | 说明                 |
| ---------- | ---- | -------------------- |
| RSI 策略   | 动量 | 超买超卖判断         |
| MACD 策略  | 趋势 | 金叉死叉信号         |
| 双均线策略 | 趋势 | 短期均线穿越长期均线 |
| 布林带策略 | 波动 | 价格触及上下轨信号   |
| 海龟策略   | 突破 | 唐奇安通道突破       |

## 回测分析

- 基础信息：回测 ID、策略版本、选股版本、参数快照
- 时间范围：开始/结束日期、实际回测耗时
- 初始设置：初始资金、手续费率、滑点设置

## 快速开始

### 环境要求

| 依赖       | 版本  | 说明         |
| ---------- | ----- | ------------ |
| Python     | 3.10+ | 后端运行环境 |
| Node.js    | 18+   | 前端构建     |
| PostgreSQL | 13+   | 主数据库     |

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/yourname/quant-stock.git
cd quant-stock

# 复制配置文件
cp .env.example .env
# 编辑 .env 填入必要配置

# 启动服务
docker-compose up -d

# 访问
# 前端: http://localhost:3000
# API:  http://localhost:8000/docs
```

### 方式二：本地开发

<details>
<summary>后端部署</summary>

```bash
cd backend

# 创建虚拟环境 (推荐使用 uv)
uv venv && source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动服务
python main.py
# 或使用 make
make api
```

</details>

<details>
<summary>前端部署</summary>

```bash
cd frontend

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 生产构建
pnpm build
```

</details>

### Docker 部署（推荐）

```bash
docker-compose up -d
```

## 📁 项目结构

```
quant-stock/
├── backend/
│   ├── app/
│   │   ├── api/            # API 路由层
│   │   │   ├── v1/         # API v1 版本
│   │   │   └── deps.py     # 依赖注入
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py   # 环境配置
│   │   │   ├── security.py # 认证加密
│   │   │   └── events.py   # 生命周期事件
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑层
│   │   ├── strategies/     # 交易策略
│   │   ├── selectors/      # 选股规则引擎
│   │   ├── backtester/     # 回测引擎
│   │   ├── notifiers/      # 通知渠道
│   │   └── tasks/          # 定时任务
│   ├── scripts/            # 脚本工具
│   ├── tests/              # 测试用例
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── composables/    # 组合式函数
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 请求封装
│   │   ├── types/          # TypeScript 类型
│   │   └── utils/          # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── docs/                   # 文档
├── docker-compose.yml
├── Makefile
└── README.md
```

## 核心技术栈

### 前端

- **框架**: Vue 3 + TypeScript + Vite
- **UI**: Arco Design Vue
- **样式**: Tailwind CSS
- **状态**: Pinia
- **图表**: ECharts

### 后端

- **框架**: FastAPI + Uvicorn
- **ORM**: Tortoise-ORM
- **回测**: Backtrader
- **调度**: APScheduler
- **数据源**: AkShare

### 基础设施

- **数据库**: PostgreSQL
- **缓存**: Redis
- **部署**: Docker + Docker Compose
- **反代**: Nginx

## 📊 数据源

| 数据源                                         | 类型   | 说明                 |   推荐度   |
| ---------------------------------------------- | ------ | -------------------- | :--------: |
| [AKShare](https://github.com/akfamily/akshare) | 开源库 | 免费、稳定、数据全面 | ⭐⭐⭐⭐⭐ |
| [Tushare](https://tushare.pro/)                | API    | 需注册积分，数据专业 |  ⭐⭐⭐⭐  |
| 腾讯财经                                       | 爬虫   | 备用方案，有反爬风险 |    ⭐⭐    |
| 新浪财经                                       | 爬虫   | 备用方案，有反爬风险 |    ⭐⭐    |

## 通知渠道

支持多渠道推送交易信号：

- 邮件 (SMTP)
- 企业微信机器人
- 钉钉机器人
- Server 酱 (微信推送)

## 📅 开发计划

### v1.0 (MVP)

- [x] 数据同步模块
- [ ] 选股器基础功能
- [ ] 3 个内置策略
- [ ] 基础回测报告
- [ ] 邮件通知

### v1.1

- [ ] 策略参数调优 (Optuna)
- [ ] 更多通知渠道
- [ ] 回测报告增强

### v2.0

- [ ] 组合策略
- [ ] 多因子选股
- [ ] 仓位管理
- [ ] 风控模块
- [ ] 模拟盘对接

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。

## ⚠️ 免责声明

> **本项目仅供学习和研究使用，不构成任何投资建议。**
>
> 股市有风险，投资需谨慎。使用本系统进行的任何投资决策，需自行承担相应风险。作者不对因使用本系统造成的任何损失负责。

---

<p align="center">
  如果这个项目对你有帮助，请点一个 ⭐ Star 支持一下！
</p>
