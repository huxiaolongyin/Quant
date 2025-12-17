from aerich import Command
from tortoise.exceptions import OperationalError

from backend.core.config import Settings
from backend.core.logger import logger


async def modify_db(config=None):
    """初始化数据库"""
    if config is None:
        config = Settings.TORTOISE_ORM

    command = Command(tortoise_config=config, app="quant")

    try:
        # 先初始化 Aerich（创建迁移历史表）
        await command.init()
        logger.info("Aerich 迁移系统初始化完成")

        # 初始化数据库（第一次运行时创建表）
        await command.init_db(safe=True)
        logger.info("数据库表结构初始化完成")

    except FileExistsError:
        logger.info("迁移配置已存在，跳过初始化")
    except Exception as e:
        logger.warning(f"初始化过程遇到问题: {e}")

    # 检测并生成迁移
    try:
        migrated = await command.migrate()
        if migrated:
            logger.info(f"数据库迁移生成完成: {migrated}")
    except Exception as e:
        logger.info(f"没有需要迁移的内容: {e}")

    # 应用迁移
    try:
        upgraded = await command.upgrade(run_in_transaction=True)
        if upgraded:
            logger.info(f"数据库升级完成: {upgraded}")
    except OperationalError as e:
        logger.error(f"数据库升级失败: {e}")
        raise e
    except Exception as e:
        logger.info(f"数据库已是最新版本: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(modify_db())
