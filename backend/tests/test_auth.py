# -*- coding: utf-8 -*-
"""认证模块测试：注册、登录、获取当前用户、权限。"""


def test_register_success(client):
    import uuid
    username = f"reg_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": username,
        "password": "pass123",
        "nickname": "张三",
    })
    assert r.status_code == 200, f"注册应成功: {r.text}"
    data = r.json()
    assert data["access_token"], "注册应返回 token"
    assert data["user"]["username"] == username
    assert data["user"]["role"] == "student"
    assert data["user"]["nickname"] == "张三"


def test_register_duplicate_username(client, db_session):
    import uuid
    from models.user import User
    username = f"dup_{uuid.uuid4().hex[:8]}"
    body = {"username": username, "password": "pass123"}
    assert client.post("/api/auth/register", json=body).status_code == 200
    # 第二次注册同名用户名应 400
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 400
    assert "用户名已被注册" in r.json()["detail"]
    # 清理
    u = db_session.query(User).filter(User.username == username).first()
    if u:
        db_session.delete(u)
        db_session.commit()


def test_register_weak_password_rejected(client):
    """密码不含数字或太短都应被拒。"""
    import uuid
    # 只有字母，无数字
    r = client.post("/api/auth/register", json={
        "username": f"w1_{uuid.uuid4().hex[:8]}",
        "password": "abcdef",
    })
    assert r.status_code == 422
    # 太短
    r = client.post("/api/auth/register", json={
        "username": f"w2_{uuid.uuid4().hex[:8]}",
        "password": "a1",
    })
    assert r.status_code == 422


def test_login_success(student_user, client):
    token, user_id = student_user
    _ = token, user_id
    # 用相同账号重新登录（student_user 已知用户名，但 fixture 未返回；这里改用 admin 验证）
    r = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert r.status_code == 200
    assert r.json()["access_token"]
    assert r.json()["user"]["role"] == "admin"


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong123"})
    assert r.status_code == 401
    assert "用户名或密码错误" in r.json()["detail"]


def test_login_nonexistent_user(client):
    r = client.post("/api/auth/login", json={"username": "no_such_user_xyz", "password": "pass123"})
    assert r.status_code == 401


def test_get_me_with_token(admin_headers, client):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_get_me_without_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_get_me_with_invalid_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401