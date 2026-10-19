# -*- coding: utf-8 -*-
"""
pytest 全局夹具

设计说明：
- 测试使用独立的 MySQL 数据库 `campus_notice_test`，绝不污染正式库 `campus_notice`。
- 通过环境变量覆盖 config（pydantic-settings 中环境变量优先级高于 .env）：
  DATABASE_NAME=campus_notice_test、DEBUG=False、REDIS_ENABLED=False。
- 环境变量必须在 import 任何 backend 模块之前设置，因此放在 conftest 顶部。
- admin 密码统一为 123456，与 main.lifespan 的默认管理员逻辑一致。
"""
import os

# 关键：必须在导入 backend 任何模块之前设置环境变量
os.environ["DATABASE_NAME"] = "campus_notice_test"
os.environ["DEBUG"] = "False"
os.environ["REDIS_ENABLED"] = "False"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"

import pytest
import pymysql

# 测试库连接信息（与 .env 中正式库同一 MySQL 实例，仅库名不同）
TEST_DB_NAME = "campus_notice_test"
MYSQL = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "19491001@Mysql!!",
}


def _create_test_database():
    conn = pymysql.connect(
        host=MYSQL["host"], port=MYSQL["port"],
        user=MYSQL["user"], password=MYSQL["password"],
        charset="utf8mb4", autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{TEST_DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()


@pytest.fixture(scope="session")
def setup_db():
    """
    建立测试库 + 清空所有表（保证测试从干净状态开始）。
    这是 client / db_session 的依赖，fixture 依赖链保证它最先执行。
    注意：不在此处建 admin，交给 TestClient 的 lifespan 统一创建（密码 123456）。
    """
    _create_test_database()

    from database import Base, engine
    import models.user  # noqa: F401
    import models.category  # noqa: F401
    import models.notice  # noqa: F401
    import models.favorite  # noqa: F401
    import models.notification  # noqa: F401
    import models.operation_log  # noqa: F401
    import models.search_log  # noqa: F401
    import models.comment  # noqa: F401
    import models.notice_like  # noqa: F401
    import models.banner  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    # 测试结束后清空表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(setup_db):
    """FastAPI TestClient，会话级复用。with 会触发 lifespan（建表 + 创建 admin）。"""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def db_session(setup_db):
    """
    直接暴露测试库 session，供断言数据落库情况。
    每次测试独立 session，并在 yield 前 commit（结束前一个事务），
    确保能读到 API 侧已提交的数据（规避 SQLAlchemy 事务缓存导致的"看不到新数据"）。
    """
    from database import SessionLocal

    db = SessionLocal()
    db.commit()  # 结束隐式事务，后续查询走新快照
    yield db
    db.rollback()
    db.close()


def _login(client, username: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"登录失败: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="session")
def admin_token(client):
    """管理员 token（admin / 123456）"""
    return _login(client, "admin", "123456")["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def student_user(client, db_session):
    """
    每次调用创建一个全新学生账号，返回 (token, user_id)。
    teardown 时清理，避免污染其它用例。
    """
    import uuid
    from models.user import User

    username = f"stu_{uuid.uuid4().hex[:10]}"
    r = client.post("/api/auth/register", json={
        "username": username,
        "password": "pass123",
        "nickname": "测试学生",
    })
    assert r.status_code == 200, f"注册失败: {r.status_code} {r.text}"
    data = r.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    yield token, user_id
    # 清理
    u = db_session.query(User).filter(User.id == user_id).first()
    if u:
        db_session.delete(u)
        db_session.commit()


@pytest.fixture()
def category(client, admin_headers):
    """创建一个测试分类，返回 category_id，teardown 清理。"""
    r = client.post("/api/categories", json={
        "name": "测试分类", "icon": "🧪", "sort_order": 99,
    }, headers=admin_headers)
    assert r.status_code == 200, f"创建分类失败: {r.status_code} {r.text}"
    cid = r.json()["id"]
    yield cid
    try:
        client.delete(f"/api/categories/{cid}", headers=admin_headers)
    except Exception:
        pass


@pytest.fixture()
def notice(client, admin_headers, category):
    """创建一个测试公告（发布状态），返回 notice_id，teardown 清理。"""
    r = client.post("/api/notices", json={
        "title": "测试公告标题",
        "content": "这是测试公告的正文内容。",
        "summary": "测试摘要",
        "category_id": category,
        "is_top": 0,
        "status": 1,
    }, headers=admin_headers)
    assert r.status_code == 200, f"创建公告失败: {r.status_code} {r.text}"
    nid = r.json()["id"]
    yield nid
    try:
        client.delete(f"/api/notices/{nid}", headers=admin_headers)
    except Exception:
        pass