import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from backend.api.router import router
from backend.core.scheduler import scheduler
from backend.db.db_init import init_default_data, modify_db
from backend.services.sync import sync_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await modify_db()
        await init_default_data()
        await sync_service.sync_holidays()  #  启动时，同步节假日信息
        scheduler.start()
        yield
    except asyncio.CancelledError:
        # 优雅地吞掉 Windows 下关闭时产生的取消异常
        pass
    finally:
        # 这里放你的清理/关闭代码（如果有的话）
        pass


app = FastAPI(title="Quant API", docs_url=None, redoc_url=None, lifespan=lifespan)


# 加载静态文件
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


# 自定义 Swagger 文档路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8654,
        reload=True,
        reload_dirs=["backend"],
    )
