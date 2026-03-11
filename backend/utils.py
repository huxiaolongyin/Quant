import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

import pandas as pd
from tortoise.expressions import Q

import backend.core.config as config
from backend.core.logger import logger
from backend.db.session import with_db
from backend.models import DailyLine, Holiday


@with_db
async def get_stock_data(stock_code: str, fromdate: datetime, todate: datetime) -> pd.DataFrame:
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


def format_code(code: str, reverse=False):
    """统一证券代码格式：sh000001 / sz000001"""
    if reverse:
        code = code.lower()
        num = code[2:]
        if code.startswith("sh"):
            return f"{num}.SH"
        elif code.startswith("sz"):
            return f"{num}.SZ"
        else:
            return code.upper()

    else:
        if code.endswith(".XSHG"):
            return "sh" + code.replace(".XSHG", "")
        elif code.endswith(".XSHE"):
            return "sz" + code.replace(".XSHE", "")
        elif code.endswith(".SH"):
            return "sh" + code.replace(".SH", "")
        elif code.endswith(".SZ"):
            return "sz" + code.replace(".SZ", "")
        else:
            return code.lower()


def date_process(start_date: str, end_date: str = "") -> Tuple[str, str]:
    """时间处理"""

    fromdate = datetime.strptime(start_date, "%Y-%m-%d")
    if not end_date:
        todate = datetime.today() + timedelta(days=1)
    else:
        todate = datetime.strptime(end_date, "%Y-%m-%d")
    return fromdate, todate


async def get_previous_trading_day(date=None):
    """获取中国股票上一个交易日"""

    if date is None:
        date = datetime.today()

    previous_day = date

    while True:
        previous_day -= timedelta(days=1)
        weekday = previous_day.weekday()  # weekday() 返回0-6，代表周一到周日

        # 跳过周末
        if weekday in (5, 6):
            continue

        # 检查是否为节假日
        holiday = await Holiday.get_or_none(date=previous_day.date())
        if holiday is None:
            return previous_day.strftime("%Y-%m-%d")


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


def to_camel_case(string: str) -> str:
    """
    将下划线命名（snake_case）转换为小驼峰命名（camelCase）

    Args:
        string: 下划线分隔的字符串

    Returns:
        小驼峰命名的字符串

    Examples:
        >>> to_camel_case("user_name")
        'userName'
        >>> to_camel_case("created_at")
        'createdAt'
        >>> to_camel_case("id")
        'id'
    """
    components = string.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


def to_snake_case(string: str) -> str:
    """
    将驼峰命名（camelCase）转换为下划线命名（snake_case）

    Args:
        string: 驼峰命名的字符串

    Returns:
        下划线分隔的字符串

    Examples:
        >>> to_snake_case("userName")
        'user_name'
        >>> to_snake_case("createdAt")
        'created_at'
    """
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()
