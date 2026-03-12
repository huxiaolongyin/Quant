# 量化股票系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Vue-3.x-green?logo=vue.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal?logo=fastapi" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

> 面向中国 A 股市场的**量化选股与回测系统**，提供可视化策略配置、智能选股、历史回测和多渠道信号推送。

---

## ✨ 功能特性

| 模块        | 描述                               | 状态 |
| ----------- | ---------------------------------- | ---- |
| ⭐ 自选行情 | 关注股票的实时/历史行情展示        | ✅   |
| 🔄 数据同步 | 自动/手动/补数同步每日行情数据     | ✅   |
| 🔍 选股器   | 可视化配置选股条件，筛选目标股票池 | ✅   |
| 🔔 通知系统 | 钉钉/企业微信/飞书机器人推送       | ✅   |
| 📊 仪表盘   | 系统概览、持仓收益、策略运行状态   | 🚧   |
| 🏭 策略工厂 | 内置 RSI、MACD、均线等策略         | 📋   |
| ⚙️ 参数调优 | 基于 Optuna 的策略参数自动优化     | 📋   |
| 📈 回测分析 | 策略回测、收益曲线、交易明细报告   | 📋   |
| ⚡ 基础配置 | 税率、手续费、通知渠道等系统设置   | 📋   |

> ✅ 已完成 | 🚧 开发中 | 📋 计划中

---

## 🚀 快速开始

### 环境要求

| 依赖        | 版本   | 说明                          |
| ----------- | ------ | ----------------------------- |
| Python      | 3.10+  | 后端运行环境                  |
| Node.js     | 18+    | 前端构建                      |
| TimescaleDB | 最新版 | 时序数据库（PostgreSQL 扩展） |

### Docker 部署（推荐）

```bash
git clone https://github.com/yourname/quant-stock.git
cd quant-stock

cp .env.example .env
# 编辑 .env 填入必要配置

docker-compose up -d

# 前端：http://localhost:3000
# API 文档：http://localhost:8654/docs
```

### 本地开发

<details>
<summary>后端部署</summary>

```bash
cd backend

python -m venv .venv && .venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt

# 初始化数据库
python -c "from backend.db.db_init import modify_db; import asyncio; asyncio.run(modify_db())"

python main.py
```

</details>

<details>
<summary>前端部署</summary>

```bash
cd frontend

pnpm install
pnpm dev
```

</details>

---

## 🎯 核心模块

### 🔍 选股器

可视化配置选股条件，筛选目标股票池。

- **版本管理**：支持选股条件版本控制
- **智能过滤**：
  - 基础字段：交易所、板块、行业、省份、城市、股票名称
  - 行情指标：最新价、成交量、成交额
  - 技术指标：涨停次数(近 30 日)、跌停次数(近 30 日)、均线(MA5/10/20)
- **缓存机制**：每天计算一次，提升性能

```yaml
选股条件示例:
  - 交易所：深圳
  - 排除：ST/*ST 股票
  - 股价：<= 50 元
  - 排除行业：房地产，建筑业
  - 排除：近 15 日内有数次涨停/跌停
```

### 🔔 通知系统

支持多渠道推送交易信号：

| 渠道              | 状态 | 说明         |
| ----------------- | ---- | ------------ |
| 💬 企业微信机器人 | ✅   | Webhook 推送 |
| 📱 钉钉机器人     | ✅   | 支持签名验证 |
| 📲 飞书机器人     | ✅   | 支持签名验证 |
| 📧 邮件 (SMTP)    | 📋   | 计划中       |
| 📲 Server 酱      | 📋   | 计划中       |

### 🏭 策略工厂

内置多种交易策略：

| 策略名称     | 类型     | 说明             |
| ------------ | -------- | ---------------- |
| RSI 策略     | 动量     | 超买超卖判断     |
| MACD 策略    | 趋势     | 金叉死叉信号     |
| 均值回归策略 | 均值回归 | 价格回归均值     |
| 动量策略     | 动量     | 趋势跟踪         |
| 量价策略     | 量价     | 成交量与价格分析 |

---

## 🛠️ 技术栈

### 前端

| 技术            | 说明                   |
| --------------- | ---------------------- |
| Vue 3           | 渐进式 JavaScript 框架 |
| TypeScript      | 类型安全               |
| Vite            | 构建工具               |
| Arco Design Vue | UI 组件库              |
| Tailwind CSS    | 原子化 CSS             |
| Pinia           | 状态管理               |
| ECharts         | 图表库                 |

### 后端

| 技术         | 说明                 |
| ------------ | -------------------- |
| FastAPI      | 现代 Python Web 框架 |
| Uvicorn      | ASGI 服务器          |
| Tortoise ORM | 异步 ORM             |
| Backtrader   | 回测框架             |
| APScheduler  | 定时任务调度         |
| AkShare      | 数据源               |

### 基础设施

| 技术        | 说明                          |
| ----------- | ----------------------------- |
| TimescaleDB | 时序数据库（PostgreSQL 扩展） |
| Docker      | 容器化部署                    |

---

## 📊 数据源

| 数据源                                         | 类型   | 说明                 | 推荐度     |
| ---------------------------------------------- | ------ | -------------------- | ---------- |
| [AKShare](https://github.com/akfamily/akshare) | 开源库 | 免费、稳定、数据全面 | ⭐⭐⭐⭐⭐ |
| [Tushare](https://tushare.pro/)                | API    | 需注册积分，数据专业 | ⭐⭐⭐⭐   |

---

## 📁 项目结构

```
quant-stock/
├── backend/
│   ├── api/                 # API 路由层
│   │   └── v1/              # API v1 版本
│   ├── core/                # 核心配置
│   ├── db/                  # 数据库初始化
│   ├── enums/               # 枚举定义
│   ├── models/              # ORM 模型
│   ├── notifiers/           # 通知渠道
│   ├── schemas/             # Pydantic 模式
│   ├── services/            # 业务逻辑层
│   ├── trading/             # 交易策略与回测
│   │   ├── strategies/      # 策略实现
│   │   └── feeds/           # 数据源
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API 请求封装
│   │   ├── components/      # 通用组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── types/           # TypeScript 类型
│   │   └── views/           # 页面组件
│   ├── package.json
│   └── vite.config.ts
├── data/                    # 数据持久化
├── docker-compose.yml
└── README.md
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。

---

## ⚠️ 免责声明

> **本项目仅供学习和研究使用，不构成任何投资建议。**
>
> 股市有风险，投资需谨慎。使用本系统进行的任何投资决策，需自行承担相应风险。作者不对因使用本系统造成的任何损失负责。

---

<p align="center">
  如果这个项目对你有帮助，请点一个 ⭐ Star 支持一下！
</p>
