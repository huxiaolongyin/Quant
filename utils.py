import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

import backtrader as bt
import pandas as pd
from tortoise.expressions import Q

import config
from core.init_app import with_db
from logger import get_logger
from models import DailyLine

logger = get_logger(__name__)


@with_db
async def __get_stock_data(
    stock_code: str, fromdate: datetime, todate: datetime
) -> pd.DataFrame:
    """数据获取与预处理函数"""

    q = Q(stock_code=stock_code) & Q(trade_date__gt=fromdate)
    q &= Q(trade_date__lt=todate)

    stock_daily_data = await DailyLine.filter(q).all()

    df = pd.DataFrame([item.__dict__ for item in stock_daily_data])

    # 时间转换及索引设置
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df.set_index("trade_date", inplace=True)

    # 数据预处理
    parse_df = df.copy()
    parse_df = parse_df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    parse_df = parse_df[["Open", "High", "Low", "Close", "Volume"]]

    parse_df.sort_index(ascending=True, inplace=True)

    return parse_df


@with_db
async def __get_price_latest(stock_code: str, date: str):
    """获取股票价格"""
    return await DailyLine.filter(stock_code=stock_code, trade_date=date).first()


def code_transform(code: str):
    """代码转换"""

    if code.endswith(".SZ"):
        code = "sz" + code[:6]
    elif code.endswith(".SH"):
        code = "sh" + code[:6]
    else:
        code = code.lower()
    return code


def date_process(start_date: str, end_date: str = "") -> Tuple[str, str]:
    """时间处理"""

    fromdate = datetime.strptime(start_date, "%Y-%m-%d")
    if not end_date:
        todate = datetime.today()
    else:
        todate = datetime.strptime(end_date, "%Y-%m-%d")
    return fromdate, todate


def get_previous_workday(date=None):
    """获取上一个工作日"""

    if date is None:
        date = datetime.today()

    offset = 1
    weekday = date.weekday()
    # weekday() 返回0-6，代表周一到周日

    if weekday == 0:  # 周一，上一个工作日是前周五，往前推3天
        offset = 3
    elif weekday == 6:  # 星期日，上一个工作日是周五，往前推2天
        offset = 2
    elif weekday == 5:  # 星期六，上一个工作日是周五，往前推1天
        offset = 1
    else:
        offset = 1  # 正常情况往前推1天即可

    previous_workday = date - timedelta(days=offset)
    return previous_workday.strftime("%Y-%m-%d")


def send_email(subject: str, body: str, to_email: str = ""):
    """使用SMTP发送邮件"""
    msg = MIMEMultipart()
    from_email = config.SMTP_USER
    if not to_email:
        to_email = from_email

    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))  # 如果想发HTML，用'html'

    try:
        # 连接SMTP服务器
        server = smtplib.SMTP("smtp.qq.com", 587)
        server.starttls()  # 启用TLS安全传输
        server.login(from_email, config.SMTP_PWD)  # 登录邮箱

        text = msg.as_string()
        server.sendmail(from_email, to_email, text)  # 发送邮件
        logger.info("Email sent successfully!")
    except Exception as e:
        logger.error("Error sending email:", e)
    finally:
        server.quit()


async def run_backtest(
    stock_code: str,
    strategy: bt.Strategy,
    start_date: str,
    end_date: str = "",
    is_plot=False,
    init_cash=10000.0,
    **kwargs,
):
    """执行回测"""
    logger.info("-" * 75)
    logger.info(
        f"回测开始: 股票={stock_code}, 策略={strategy.__qualname__}, 开始日期={start_date}, 参数={kwargs}"
    )
    stock_code = code_transform(stock_code)

    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    # 时间处理
    fromdate, todate = date_process(start_date, end_date)

    # 获取数据
    stock_data = await __get_stock_data(stock_code, fromdate, todate)

    data = bt.feeds.PandasData(
        dataname=stock_data,
        fromdate=fromdate,
        todate=todate,
        name=stock_code,
    )
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(strategy, **kwargs)

    # 设置初始资金
    cerebro.broker.setcash(init_cash)

    # 设置佣金
    cerebro.broker.setcommission(commission=0.0005)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

    # 运行回测
    results = cerebro.run()
    strat = results[0]

    # 输出结果
    if cerebro.broker.getvalue() == init_cash:
        logger.warning("回测未产生交易，可能是数据或策略设置问题。")

        return 10000, 0.0, 0.0  # 返回初始资金和收益率为0
    else:
        final_asset = round(cerebro.broker.getvalue(), 2)
        drawdown = strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]
        returns = strat.analyzers.returns.get_analysis()["rnorm100"]
        try:
            sharpe = round(strat.analyzers.sharpe.get_analysis()["sharperatio"], 3)
        except:
            sharpe = None

        logger.info(
            f"最终资产={final_asset}, 夏普比率={sharpe}, 最大回撤={drawdown:.2f}%, 年化收益率={returns:.2f}%"
        )

        # 绘制结果
        if is_plot:
            cerebro.plot(style="candlestick")

        return (
            stock_code,
            start_date,
            end_date,
            strategy.__name__,
            final_asset,
            f"{returns:.2f}%",
        )


# if __name__ == "__main__":
#     import asyncio

#     print(asyncio.run(__get_stock_data("sh601212", start_date="2025-05-03")))
if __name__ == "__main__":
    from strategy.rsi import RSIStrategy

    send_email(buy_or_sell="buy", stock_code="sz002980", strategy=RSIStrategy)
