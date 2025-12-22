import datetime
from functools import lru_cache

import pandas as pd
import requests

from backend.core.logger import logger
from backend.utils import format_code
from cachetools import cached, TTLCache


# 全局 Session，复用 TCP 连接，统一 Header
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
)

# 创建全局缓存对象
_today_minutes_cache = TTLCache(maxsize=256, ttl=60)


def _process_dataframe(data, columns):
    """统一处理 DataFrame 格式：类型转换、索引设置"""
    df = pd.DataFrame(data, columns=columns)

    # 自动转换数值类型
    cols_to_float = ["open", "close", "high", "low", "volume"]
    df[cols_to_float] = df[cols_to_float].astype(float)

    # 处理时间索引
    time_col = columns[0]  # 通常是 'day' 或 'time'
    df[time_col] = pd.to_datetime(df[time_col])
    df.set_index(time_col, inplace=True)
    df.index.name = ""
    return df


def get_price_tx(code: str, end_date: str = "", count: int = 10, frequency: str = "1d"):
    """腾讯数据源：支持日线及分钟线"""
    unit_map = {"1d": "day", "1w": "week", "1M": "month"}

    # 处理日期
    if not end_date or end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
        end_date = ""

    else:
        end_date = (
            end_date.strftime("%Y-%m-%d")
            if isinstance(end_date, datetime.date)
            else end_date.split(" ")[0]
        )

    # 分支：日线/周线/月线
    if frequency in unit_map:
        unit = unit_map[frequency]
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},{unit},,{end_date},{count},qfq"
        resp = SESSION.get(url, timeout=10)
        resp.raise_for_status()

        data_json = resp.json()
        ms = "qfq" + unit
        stk_data = data_json["data"].get(code)
        # 优先取前复权数据，没有则取不复权
        buf = stk_data.get(ms, stk_data.get(unit, []))

        # 前复权可能有7个数据，只取前6个
        buf = [b[:6] for b in buf]
        return _process_dataframe(
            buf, columns=["time", "open", "close", "high", "low", "volume"]
        )

    # 分支：分钟线
    else:
        ts = int(frequency[:-1])  # 解析 1m, 5m, 15m...
        url = f"http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={code},m{ts},,{count}"
        resp = SESSION.get(url, timeout=10)
        resp.raise_for_status()

        data_json = resp.json()
        buf = data_json["data"][code]["m" + str(ts)]

        # 腾讯分钟线返回的数据列较多，只要前6列
        df = _process_dataframe(
            buf, columns=["time", "open", "close", "high", "low", "volume", "n1", "n2"]
        )
        df = df.iloc[:, :5]  # 只要 OHLCV

        # 修正最新即时价格 (qt 数据)
        latest_price = float(data_json["data"][code]["qt"][code][3])
        df.iloc[-1, df.columns.get_loc("close")] = latest_price
        return df


# 新浪接口
def get_price_sina(code, end_date="", count=10, frequency="60m"):
    """新浪数据源：支持全周期"""
    # 频率映射
    freq_map = {"1d": "240m", "1w": "1200m", "1M": "7200m"}
    sina_freq = freq_map.get(frequency, frequency)

    # 计算 scale (分钟数)
    scale = int(sina_freq[:-1])

    # 处理带结束日期的 count 补偿逻辑
    original_count = count
    if end_date and frequency in ["1d", "1w", "1M", "240m", "1200m", "7200m"]:
        dt_end = (
            pd.to_datetime(end_date)
            if not isinstance(end_date, datetime.date)
            else pd.to_datetime(end_date)
        )
        # 估算需要多请求多少条数据才能覆盖到 end_date
        diff_days = (datetime.datetime.now() - dt_end).days
        # 粗略估算：周线除以4，月线除以29，其他按日
        factor = 4 if "w" in frequency else (29 if "M" in frequency else 1)
        count += (diff_days // factor) + 5  # +5 buffer

    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale={scale}&ma=5&datalen={count}"

    resp = SESSION.get(url, timeout=10)
    resp.raise_for_status()

    data_json = resp.json()
    if not data_json:
        raise ValueError(f"Sina API returned empty data for {code}")

    df = _process_dataframe(
        data_json, columns=["day", "open", "high", "low", "close", "volume"]
    )

    # 如果指定了 end_date，进行切片
    if end_date:
        df = df[df.index <= end_date]
        return df.iloc[-original_count:]

    return df


def get_price(code, end_date="", count=10, frequency="1d", fields=[]):
    """
    对外统一接口
    Args:
        code: 证券代码 (e.g. 'sh000001', '600519.XSHG')
        end_date: 结束日期
        count: 数据长度
        frequency: 周期 ('1m', '5m', '15m', '30m', '60m', '1d', '1w', '1M')
    """
    xcode = format_code(code)

    # 策略配置：定义不同周期的首选和备选源
    # 1m 只有腾讯有
    if frequency == "1m":
        return get_price_tx(xcode, end_date, count, frequency)

    # 其他周期：默认首选新浪，备选腾讯
    primary = get_price_sina
    backup = get_price_tx

    # 如果是腾讯更擅长的日/周/月，也可以配置为腾讯优先，但保持原逻辑新浪优先
    try:
        return primary(xcode, end_date=end_date, count=count, frequency=frequency)
    except (requests.RequestException, ValueError, KeyError) as e:
        # 调试时可开启
        # logger.debug(f"Primary source failed: {e}, switching to backup...")
        try:
            return backup(xcode, end_date=end_date, count=count, frequency=frequency)
        except Exception as e_backup:
            logger.error(f"All sources failed for code: {code}. Error: {e_backup}")
            return pd.DataFrame()  # 返回空DF避免程序Crash


@cached(cache=_today_minutes_cache)
def _get_today_minutes(code: str) -> dict:
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
    bars = (
        df_latest.rename_axis("datetime")
        .reset_index()
        .assign(time=lambda x: x["datetime"].dt.strftime("%H:%M"))[
            ["time", "open", "close", "high", "low", "volume"]
        ]
        .to_dict("records")
    )

    return pre_close, bars


def get_price_quotes(
    holding_stocks: list[(str, str)], force_refresh: bool = False
) -> list[dict[str, any]]:
    """
    获取多个股票今日分钟级别数据

    Args:
        holding_stocks: 股票代码列表，如 [('600519.SH', 100), ('000001.SZ', 200)]
        force_refresh: 是否强制刷新缓存

    Returns:
        {
            "600519.SH": [{"time": "09:30", "open":100, "close": 1800.5}, ...],
            "000001.SZ": [{"time": "09:30", "open":100, "close": 10.67}, ...]
        }
    """
    # 强制刷新时清空缓存

    if force_refresh:
        _today_minutes_cache.clear()

    res = []
    for holding_stock in holding_stocks:
        stock_name, holding_num = holding_stock
        pre_close, bars = _get_today_minutes(stock_name)

        # 最新价
        latest = bars[-1]
        latest_price = latest["close"]

        # 计算涨跌
        change = round(latest_price - pre_close, 4)
        change_percent = round((change / pre_close) * 100, 2) if pre_close else 0

        # 汇总统计
        total_volume = sum(bar["volume"] for bar in bars)
        high = max(bar["close"] for bar in bars)
        low = min(bar["close"] for bar in bars)

        # 持仓市值
        price = holding_num * latest_price

        # 昨日持仓市值
        yesterday_price = holding_num * pre_close
        res.append(
            {
                "stockCode": stock_name,
                "latestPrice": latest_price,
                "preClose": pre_close,
                "change": change,
                "changePercent": change_percent,
                "open": bars[0]["open"],
                "high": high,
                "low": low,
                "volume": total_volume,
                "price": price,
                "yesterdayPrice": yesterday_price,
                "bars": bars,  # 分时明细
            }
        )
    return res


if __name__ == "__main__":
    # 测试代码
    try:
        # print("=== 上证指数日线 (Sina优先) ===")
        # df_day = get_price("sh000001", frequency="1d", count=5)
        # print(df_day)

        # print("\n=== 平安银行15分钟线 (Sina优先) ===")
        # df_min = get_price("000001.XSHE", frequency="15m", count=5)
        # print(df_min)

        # print("\n=== 腾讯1分钟线 (只有腾讯) ===")
        # df_1m = get_price("sh000001", frequency="1m", count=5)
        # print(df_1m)
        df_1d = get_price_tx("sh000001", frequency="1d", count=5)
        print(df_1d)
    except Exception as e:
        print(f"Test failed: {e}")
