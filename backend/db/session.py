import functools
from contextlib import asynccontextmanager

from tortoise import Tortoise

from backend.core.config import Settings


@asynccontextmanager
async def db_context():
    await Tortoise.init(config=Settings.TORTOISE_ORM)
    try:
        yield
    finally:
        await Tortoise.close_connections()


def with_db(func):
    """数据库连接装饰器"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with db_context():
            return await func(*args, **kwargs)

    return wrapper
