import sys

from loguru import logger

# 移除默认的 handler (避免重复打印)
logger.remove()

# 1. 输出到控制台 (开发环境看)
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level}</level> - <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# 2. 输出到文件
logger.add(
    "logs/quant_{time:YYYY-MM-DD}.log",  # 日志文件路径
    rotation="00:00",  # 每天凌晨切割
    retention="30 days",  # 保留30天
    level="INFO",
    encoding="utf-8",
    enqueue=True,  # 异步写入，防止阻塞主线程
)
