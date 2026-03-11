from datetime import date, datetime
from typing import List, Literal

import requests
from cachetools import TTLCache, cached

from backend.core.logger import logger
from backend.schemas.market import DateBar, MinuteBar, StockQuote
from backend.utils import format_code

# 全局 Session，复用 TCP 连接，统一 Header
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
    }
)

# 创建全局缓存对象
_today_minutes_cache = TTLCache(maxsize=256, ttl=60)


def _normalize_end_date(end_date: str | date | datetime | None) -> str:
    """
    腾讯接口 end_date:
    - 传 "" 表示取最新往前 count 条
    - 传 "YYYY-MM-DD" 表示以该日期为截止
    """
    if not end_date:
        return ""

    parsed_date = None

    if isinstance(end_date, datetime):
        parsed_date = end_date.date()
    elif isinstance(end_date, date):
        parsed_date = end_date
    elif isinstance(end_date, str):
        # 兼容 "YYYY/MM/DD" -> "YYYY-MM-DD"
        # 兼容截取带时间的字符串 "YYYY-MM-DD HH:MM:SS" -> "YYYY-MM-DD"
        date_str = end_date.replace("/", "-").split(" ")[0]
        try:
            # 严格验证日期格式和合法性 (例如 02-30 会在此处报错)
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日期格式错误: '{end_date}', 支持的格式如 '2024-02-05', '2024/02/05' 等")
    else:
        raise TypeError("end_date 必须是 str, date, datetime 或 None")

    # 如果是“今天”，腾讯接口一般也用空串更稳
    if parsed_date == date.today():
        return ""

    return parsed_date.strftime("%Y-%m-%d")


def _request_json(url: str) -> dict:
    """发送 GET 请求，返回解析后的 JSON，失败则抛出异常。"""
    resp = SESSION.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _fetch_tx_daily(code: str, end_date: str, count: int, unit: str) -> list[list]:
    """拉取日/周/月线原始数据，返回 [[date, open, close, high, low, vol], ...]"""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get" f"?param={code},{unit},,{end_date},{count},qfq"
    data = _request_json(url)["data"][code]

    # 优先取前复权，无则取不复权
    rows = data.get(f"qfq{unit}") or data.get(unit, [])
    # 截取前 6 列：[date, open, close, high, low, volume]
    return [row[:6] for row in rows]


def _fetch_tx_minute(code: str, end_date: str, count: int, frequency: str) -> list[list]:
    """拉取分钟线原始数据，返回 [[datetime, open, close, high, low, vol], ...]"""
    ts = int(frequency.rstrip("m"))
    url = f"http://ifzq.gtimg.cn/appstock/app/kline/mkline" f"?param={code},m{ts},,{count}"
    data = _request_json(url)["data"][code]
    rows = data[f"m{ts}"]

    # 只取前 6 列，修正最后一条的收盘价为即时价
    rows = [row[:6] for row in rows]
    latest_price = float(data["qt"][code][3])
    rows[-1][2] = latest_price  # index 2 = close

    return rows


def _to_date_bars(rows: list[list], code: str) -> List[DateBar]:
    """将原始行数据列表转换为 DateBar 列表。"""
    result = []
    for row in rows:
        raw_date, open_, close, high, low, volume = row
        result.append(
            DateBar(
                stock_code=format_code(code, reverse=True),
                trade_date=datetime.strptime(str(raw_date).split(" ")[0], "%Y-%m-%d").date(),
                open_=float(open_),
                close=float(close),
                high=float(high),
                low=float(low),
                volume=int(float(volume)),
                turnover=None,
            )
        )
    return result


def _to_minute_bars(rows: list[list]) -> MinuteBar:
    """将原始行数据列表转换为 MinuteBar 列表。"""
    result = []
    for row in rows:
        time, open_, close, high, low, volume = row
        result.append(
            MinuteBar(
                time=datetime.strptime(time, "%Y%m%d%H%M%S"),
                open_=float(open_),
                close=float(close),
                high=float(high),
                low=float(low),
                volume=int(float(volume)),
            )
        )
    return result


def _calc_fetch_count(count: int, end_date: str, frequency: str) -> int:
    """
    当指定 end_date 时，新浪 API 不支持按截止日过滤，
    需要多拉一些数据，再在本地截断。此函数估算实际应请求的条数。
    """
    DAILY_FREQS = {"1d", "1w", "1M", "240m", "1200m", "7200m"}
    if not end_date or frequency not in DAILY_FREQS:
        return count
    if end_date:
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        diff_days = (datetime.now() - dt_end).days
    else:
        diff_days = 0

    # 按频率折算天数差距为"条数"差距
    factor = 4 if "w" in frequency else (29 if "M" in frequency else 1)
    extra = diff_days // factor + 5  # +5 作为缓冲

    return count + extra


def _fetch_sina(code: str, scale: int, count: int) -> list[dict]:
    """调用新浪 API，返回原始 JSON 列表。"""
    url = (
        f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
        f"/CN_MarketData.getKLineData"
        f"?symbol={code}&scale={scale}&ma=5&datalen={count}"
    )
    data = _request_json(url)  # 复用之前定义的辅助函数
    if not data:
        raise ValueError(f"Sina API returned empty data for {code}")
    return data


def _to_date_bars_sina(rows: list[dict], code: str) -> List[DateBar]:
    """将新浪原始行数据（dict 列表）转换为 DateBar 列表。"""
    result = []
    for row in rows:
        result.append(
            DateBar(
                stock_code=format_code(code, reverse=True),
                trade_date=datetime.strptime(row["day"].split(" ")[0], "%Y-%m-%d").date(),
                open=float(row["open"]),
                close=float(row["close"]),
                high=float(row["high"]),
                low=float(row["low"]),
                volume=int(float(row["volume"])),
                turnover=None,
            )
        )
    return result


def get_price_tx(
    code: str,
    end_date: str | None = None,
    count: int = 10,
    frequency: str = "1d",
) -> List[DateBar | MinuteBar | None]:
    """
    腾讯数据源获取股票行情，支持日/周/月线及分钟线。
    """
    FREQ_MAP = {"1d": "day", "1w": "week", "1M": "month"}

    if frequency in FREQ_MAP:
        raw = _fetch_tx_daily(code, end_date, count, unit=FREQ_MAP[frequency])
        result = _to_date_bars(raw, code)
    else:
        raw = _fetch_tx_minute(code, end_date, count, frequency)
        result = _to_minute_bars(raw)

    return result


# 新浪接口
def get_price_sina(
    code: str,
    end_date: str = "",
    count: int = 10,
    frequency: str = "60m",
) -> List[DateBar]:
    """
    新浪数据源获取股票行情，支持全周期。
    """
    FREQ_MAP = {"1d": "240m", "1w": "1200m", "1M": "7200m"}
    sina_freq = FREQ_MAP.get(frequency, frequency)
    scale = int(sina_freq.rstrip("m"))

    fetch_count = _calc_fetch_count(count, end_date, frequency)
    raw = _fetch_sina(code, scale, fetch_count)

    bars = _to_date_bars_sina(raw, code)

    if end_date:
        bars = [b for b in bars if b.trade_date <= datetime.strptime(end_date, "%Y-%m-%d").date()]

    return bars[-count:]


def get_price(
    code: str,
    end_date: str | date | datetime | None = None,
    count: int = 1,
    frequency: Literal["1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M"] = "1d",
) -> List[DateBar | MinuteBar | None]:
    """
    获取指定证券的历史行情（K线）数据对外统一接口。

    Args:
        code: 证券代码 (e.g. 'sh000001', '600519.XSHG')
        end_date: 结束日期 (e.g. '2024-02-05', '2024/02/05', '2024-02-05 14:30:00')
        count: 获取的 K 线数据条数（期望的数据长度）
        frequency: K 线周期频率. 分钟线(e.g. "1m", "5m", "15m", "30m", "60m"). 日线及以上(e.g. "1d" (日线), "1w" (周线), "1M" (月线))

    Returns:
        包含行情 Bar 数据的列表。如果所有数据源均获取失败，则返回空列表 []。
    """
    # 1. 格式化股票格式和时间
    formatted_code = format_code(code)
    end_date_str = _normalize_end_date(end_date)

    # 2. 获取数据
    # 周期频率为：1m 只有腾讯有
    if frequency == "1m":
        return get_price_tx(formatted_code, end_date_str, count, frequency)

    # 其它频率：腾讯优先，新浪作为备用
    try:
        return get_price_tx(formatted_code, end_date_str, count=count, frequency=frequency)

    except (requests.RequestException, ValueError, KeyError) as e:
        # 使用 warning 记录降级事件，方便后续排查新浪接口稳定性
        logger.warning(f"Primary source (Sina) failed for {code}: {e}, switching to backup (Tencent)...")
        try:
            return get_price_sina(formatted_code, end_date_str, count=count, frequency=frequency)

        except Exception as e_backup:
            logger.error(f"All sources failed for code: {code}. Error: {e_backup}")
            return []


@cached(cache=_today_minutes_cache)
def _get_today_minutes(code: str) -> tuple[float, List[MinuteBar]]:
    """
    获取单个股票最新交易日分钟数据（带60秒缓存）

    Args:
        code: 股票代码

    Returns:
        pre_close: 昨收价
        bars: 最新一天的分钟交易信息
    """
    formatted_code = format_code(code)
    df = get_price(formatted_code, count=250, frequency="1m")

    if df is None or df.empty:
        return {"pre_close": None, "bars": []}

    # 获取数据中最新的交易日
    latest_date = df.index[-1].date()

    # 筛选最新交易日的数据
    df_latest = df[df.index.date == latest_date]

    # 获取昨收价（最新交易日之前的最后一根K线收盘价）
    df_previous = df[df.index.date < latest_date]

    pre_close = df_previous["close"].iloc[-1] if not df_previous.empty else None

    # 构建分钟K线数据
    bars = [
        MinuteBar(
            time=row["datetime"].strftime("%H:%M"),
            open=row["open"],
            close=row["close"],
            high=row["high"],
            low=row["low"],
            volume=row["volume"],
        )
        for _, row in df_latest.reset_index(names="datetime").iterrows()
    ]

    return pre_close, bars


def get_price_quotes(holding_stocks: list[(str, str)], force_refresh: bool = False) -> list[StockQuote]:
    """
    获取多个股票今日分钟级别数据

    Args:
        holding_stocks: 股票代码列表，如 [('600519.SH', 100), ('000001.SZ', 200)]
        force_refresh: 是否强制刷新缓存
    """
    # 强制刷新时清空缓存
    if force_refresh:
        _today_minutes_cache.clear()

    res = []
    for holding_stock in holding_stocks:
        code, holding_num = holding_stock
        pre_close, bars = _get_today_minutes(code)

        # 最新价格
        latest_price = bars[-1].close

        # 计算涨跌
        change = round(latest_price - pre_close, 4)
        change_percent = round((change / pre_close) * 100, 2) if pre_close else 0

        # 汇总统计
        total_volume = sum(bar.volume for bar in bars)
        high = max(bar.close for bar in bars)
        low = min(bar.close for bar in bars)

        # 持仓市值
        market_value = holding_num * latest_price

        # 昨日持仓市值
        pre_market_value = holding_num * pre_close
        res.append(
            StockQuote(
                code=code,
                latest_price=latest_price,
                pre_close=pre_close,
                change=change,
                change_percent=change_percent,
                open=bars[0].open,
                high=high,
                low=low,
                volume=total_volume,
                holding_num=holding_num,
                market_value=market_value,
                pre_market_value=pre_market_value,
                bars=bars,
            )
        )
    return res


if __name__ == "__main__":
    data = get_price("002106.SZ", frequency="1d", end_date="2026-02-26", count=5)
    print(data)
    print(len(data))
    # # 测试代码
    # try:
    #     # print("=== 上证指数日线 (Sina优先) ===")
    #     # df_day = get_price("sh000001", frequency="1d", count=5)
    #     # print(df_day)

    #     # print("\n=== 平安银行15分钟线 (Sina优先) ===")
    #     # df_min = get_price("000001.XSHE", frequency="15m", count=5)
    #     # print(df_min)

    #     # print("\n=== 腾讯1分钟线 (只有腾讯) ===")
    #     # df_1m = get_price("sh000001", frequency="1m", count=5)
    #     # print(df_1m)
    #     # df_1d = get_price_tx("sh000001", frequency="1d", count=5)
    #     # print(df_1d)
    #     data = get_price("000627.SZ", end_date="2026-02-23", count=2)
    #     print(data)
    # except Exception as e:
    #     print(f"Test failed: {e}")
