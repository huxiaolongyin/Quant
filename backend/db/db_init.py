from aerich import Command
from tortoise.exceptions import OperationalError

from backend.core.config import Settings
from backend.core.logger import logger


async def init_default_data():
    """初始化默认数据：权限、角色、管理员账户"""
    from backend.models.user import Permission, Role, User
    from backend.core.auth import get_password_hash

    permissions_data = [
        {"name": "用户管理", "code": "user", "module": "system", "type": "menu", "sort": 1},
        {"name": "用户查看", "code": "user:view", "module": "system", "type": "button", "sort": 1},
        {"name": "用户新增", "code": "user:create", "module": "system", "type": "button", "sort": 2},
        {"name": "用户编辑", "code": "user:update", "module": "system", "type": "button", "sort": 3},
        {"name": "用户删除", "code": "user:delete", "module": "system", "type": "button", "sort": 4},
        {"name": "角色管理", "code": "role", "module": "system", "type": "menu", "sort": 2},
        {"name": "角色查看", "code": "role:view", "module": "system", "type": "button", "sort": 1},
        {"name": "角色新增", "code": "role:create", "module": "system", "type": "button", "sort": 2},
        {"name": "角色编辑", "code": "role:update", "module": "system", "type": "button", "sort": 3},
        {"name": "角色删除", "code": "role:delete", "module": "system", "type": "button", "sort": 4},
        {"name": "策略管理", "code": "strategy", "module": "trading", "type": "menu", "sort": 1},
        {"name": "策略查看", "code": "strategy:view", "module": "trading", "type": "button", "sort": 1},
        {"name": "策略新增", "code": "strategy:create", "module": "trading", "type": "button", "sort": 2},
        {"name": "策略编辑", "code": "strategy:update", "module": "trading", "type": "button", "sort": 3},
        {"name": "策略删除", "code": "strategy:delete", "module": "trading", "type": "button", "sort": 4},
        {"name": "选股器", "code": "selector", "module": "trading", "type": "menu", "sort": 2},
        {"name": "选股器查看", "code": "selector:view", "module": "trading", "type": "button", "sort": 1},
        {"name": "选股器新增", "code": "selector:create", "module": "trading", "type": "button", "sort": 2},
        {"name": "选股器编辑", "code": "selector:update", "module": "trading", "type": "button", "sort": 3},
        {"name": "选股器删除", "code": "selector:delete", "module": "trading", "type": "button", "sort": 4},
        {"name": "数据同步", "code": "sync", "module": "data", "type": "menu", "sort": 1},
        {"name": "自选股", "code": "watchlist", "module": "data", "type": "menu", "sort": 2},
    ]

    created_permissions = []
    for perm_data in permissions_data:
        perm, created = await Permission.get_or_create(
            code=perm_data["code"],
            defaults=perm_data
        )
        if created:
            created_permissions.append(perm.code)

    if created_permissions:
        logger.info(f"创建权限: {created_permissions}")

    all_permissions = await Permission.all()

    admin_role, created = await Role.get_or_create(
        code="admin",
        defaults={
            "name": "超级管理员",
            "description": "拥有所有权限",
            "status": 1,
            "sort": 1
        }
    )
    if created:
        await admin_role.permissions.add(*all_permissions)
        logger.info("创建超级管理员角色")

    user_role, created = await Role.get_or_create(
        code="user",
        defaults={
            "name": "普通用户",
            "description": "基础访问权限",
            "status": 1,
            "sort": 2
        }
    )
    if created:
        user_perms = await Permission.filter(code__in=[
            "user", "user:view",
            "strategy", "strategy:view", "strategy:create", "strategy:update",
            "selector", "selector:view", "selector:create", "selector:update",
            "sync", "watchlist"
        ])
        await user_role.permissions.add(*user_perms)
        logger.info("创建普通用户角色")

    admin_user, created = await User.get_or_create(
        username="admin",
        defaults={
            "password": get_password_hash("admin123"),
            "email": "admin@quant.com",
            "nickname": "超级管理员",
            "status": 1,
            "is_superuser": True
        }
    )
    if created:
        await admin_user.roles.add(admin_role)
        logger.info("创建超级管理员账户: admin / admin123")

    return {
        "permissions": len(created_permissions),
        "roles": 2 if admin_role else 0,
        "admin_created": created
    }


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
