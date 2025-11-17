import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

# 数据库
POSTGRESQL_DATABASE = os.environ.get("POSTGRESQL_DATABASE")
POSTGRESQL_HOST = os.environ.get("POSTGRESQL_HOST")
POSTGRESQL_PORT = os.environ.get("POSTGRESQL_PORT")
POSTGRESQL_PASSWORD = os.environ.get("POSTGRESQL_PASSWORD")

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
                "models",
            ],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}
