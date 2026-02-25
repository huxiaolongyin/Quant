from datetime import date, datetime

import httpx

from backend.core.logger import logger
from backend.models import Holiday


async def sync_holidays():
    """同步节假日数据"""

    current_year = datetime.now().year
    year_start = date(current_year, 1, 1)
    year_end = date(current_year + 1, 1, 1)

    # 如果有今年的数据则跳过
    existing = await Holiday.filter(date__gte=year_start, date__lt=year_end).exists()
    if existing:
        logger.info(f"已存在{current_year}节假日信息，跳过同步")
        return

    url = f"https://publicapi.xiaoai.me/holiday/year?date={current_year}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    data = data.get("data", [])
    # 返回格式：[{"daytype": 1, "holiday": "元旦节", "rest": 1, "date": "2026-01-01", "week": 4, "week_desc_en": "Thursday", "week_desc_cn": "星期四" }...]

    holidays = [item for item in data if item.get("rest") == 1]

    for holiday in holidays:
        await Holiday.update_or_create(date=holiday["date"], defaults={"name": holiday["holiday"]})
    logger.info(f"{current_year}节假日信息同步完成")
