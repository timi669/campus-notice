# -*- coding: utf-8 -*-
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import Base, engine


def init_db_tables():
    import models.user
    import models.category
    import models.notice
    import models.favorite
    import models.notification
    import models.operation_log
    import models.search_log
    import models.comment
    import models.notice_like
    import models.banner
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 安全警告：检测是否使用了默认 SECRET_KEY
    if settings.SECRET_KEY == "your-secret-key-change-in-production-please-use-long-random-string":
        print("\033[93m[WARNING] 检测到使用默认 SECRET_KEY，生产环境请务必在 .env 中修改为随机长字符串！\033[0m")
    init_db_tables()
    from database import SessionLocal
    from models.user import User
    from utils.auth import hash_password
    db = SessionLocal()
    try:
        # 检测全文检索是否可用
        from routers.notice import check_fulltext_available
        check_fulltext_available(db)

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password=hash_password("123456"),
                nickname="系统管理员",
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("已创建默认管理员账号: admin / 123456")
    finally:
        db.close()
    yield
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="简易校园公告资讯小程序 - Python后端API",
    lifespan=lifespan,
)

_cors = settings.CORS_ORIGINS
origins = [o.strip() for o in _cors.split(",")] if _cors and _cors != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if _cors != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    traceback.print_exc()
    # HTTPException 直接透传其状态码和 detail
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": exc.detail, "data": None},
        )
    # 其他异常不泄露内部细节，仅记录日志
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


@app.get("/", tags=["健康检查"])
def root():
    return {"code": 0, "message": "ok", "data": {"app": settings.APP_NAME, "version": settings.APP_VERSION}}


@app.get("/health", tags=["健康检查"])
def health():
    return {"status": "ok"}


from routers.auth import router as auth_router
from routers.user import router as user_router
from routers.category import router as category_router
from routers.notice import router as notice_router
from routers.stats import router as stats_router
from routers.upload import router as upload_router
from routers.notification import router as notification_router
from routers.operation_log import router as operation_log_router
from routers.comment import router as comment_router
from routers.banner import router as banner_router

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(category_router)
app.include_router(notice_router)
app.include_router(stats_router)
app.include_router(upload_router)
app.include_router(notification_router)
app.include_router(operation_log_router)
app.include_router(comment_router)
app.include_router(banner_router)

# 挂载上传文件静态目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
