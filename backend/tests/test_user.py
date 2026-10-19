# -*- coding: utf-8 -*-
"""用户管理 + 权限测试。"""


def test_list_users_requires_admin(client):
    r = client.get("/api/users")
    assert r.status_code == 401


def test_list_users_as_admin(client, admin_headers):
    r = client.get("/api/users", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert "items" in data


def test_student_cannot_list_users(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/users", headers=headers)
    assert r.status_code == 403


def test_update_self_nickname(client, student_user):
    token, user_id = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.put("/api/users/me", json={"nickname": "新昵称"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["nickname"] == "新昵称"


def test_change_password_requires_old(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    # 旧密码错误
    r = client.put("/api/users/me/password", json={
        "old_password": "wrong_pass",
        "new_password": "newpass123",
    }, headers=headers)
    assert r.status_code == 400
    assert "旧密码不正确" in r.json()["detail"]


def test_admin_role_management(client, admin_headers, db_session):
    import uuid
    from models.user import User
    # 注册一个学生
    username = f"role_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={"username": username, "password": "pass123"})
    uid = r.json()["user"]["id"]
    # 升级为 admin
    r = client.put(f"/api/users/{uid}/role", json={"role": "admin"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    # 降回 student
    r = client.put(f"/api/users/{uid}/role", json={"role": "student"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["role"] == "student"
    # 清理
    u = db_session.query(User).filter(User.id == uid).first()
    if u:
        db_session.delete(u)
        db_session.commit()


def test_admin_cannot_demote_self(client, admin_headers, db_session):
    from models.user import User
    admin = db_session.query(User).filter(User.username == "admin").first()
    r = client.put(f"/api/users/{admin.id}/role", json={"role": "student"}, headers=admin_headers)
    assert r.status_code == 400


def test_admin_cannot_delete_self(client, admin_headers, db_session):
    from models.user import User
    admin = db_session.query(User).filter(User.username == "admin").first()
    r = client.delete(f"/api/users/{admin.id}", headers=admin_headers)
    assert r.status_code == 400


def test_admin_delete_student(client, admin_headers):
    import uuid
    username = f"del_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={"username": username, "password": "pass123"})
    uid = r.json()["user"]["id"]
    dr = client.delete(f"/api/users/{uid}", headers=admin_headers)
    assert dr.status_code == 204