import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)


class Settings:
    # 数据库
    POSTGRESQL_DATABASE = os.environ.get("POSTGRESQL_DATABASE")
    POSTGRESQL_HOST = os.environ.get("POSTGRESQL_HOST")
    POSTGRESQL_PORT = os.environ.get("POSTGRESQL_PORT")
    POSTGRESQL_PASSWORD = os.environ.get("POSTGRESQL_PASSWORD")

    # SMTP邮箱
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PWD = os.environ.get("SMTP_PWD")

    # 股票配置
    INIT_CACHE = float(os.environ.get("COMMISSION") or 10000.00)
    COMMISSION = os.environ.get("COMMISSION") or 0.0005

    # TORTOISE 配置
    TORTOISE_ORM = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "database": POSTGRESQL_DATABASE,
                    "host": POSTGRESQL_HOST,
                    "port": POSTGRESQL_PORT,
                    "user": "postgres",
                    "password": POSTGRESQL_PASSWORD,
                },
            },
        },
        "apps": {
            "quant": {
                "models": [
                    "aerich.models",
                    "backend.models",
                ],
                "default_connection": "default",
            },
        },
        "use_tz": False,
        "timezone": "Asia/Shanghai",
    }
