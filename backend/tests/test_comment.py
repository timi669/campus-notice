# -*- coding: utf-8 -*-
"""评论模块测试：列表、发布、删除权限。"""


def test_comment_list_public(client, notice):
    """评论列表无需登录即可查看。"""
    r = client.get("/api/comments", params={"notice_id": notice})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_comment_requires_login(client, notice):
    r = client.post("/api/comments", json={"notice_id": notice, "content": "匿名评论"})
    assert r.status_code == 401


def test_create_comment(client, student_user, notice):
    token, uid = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/comments", json={
        "notice_id": notice, "content": "这是一条测试评论",
    }, headers=headers)
    assert r.status_code == 200, f"发评论应成功: {r.text}"
    data = r.json()
    assert data["content"] == "这是一条测试评论"
    assert data["user_id"] == uid
    assert data["user"]["username"].startswith("stu_")
    # 列表应能看到
    rl = client.get("/api/comments", params={"notice_id": notice})
    assert rl.status_code == 200
    assert rl.json()["total"] >= 1
    ids = [c["id"] for c in rl.json()["items"]]
    assert data["id"] in ids


def test_create_comment_on_missing_notice(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/comments", json={
        "notice_id": 999999, "content": "评论不存在的公告",
    }, headers=headers)
    assert r.status_code == 404


def test_delete_own_comment(client, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    # 先发一条
    r = client.post("/api/comments", json={
        "notice_id": notice, "content": "待删除的评论",
    }, headers=headers)
    cid = r.json()["id"]
    # 本人删除
    dr = client.delete(f"/api/comments/{cid}", headers=headers)
    assert dr.status_code == 204
    # 列表应减少
    rl = client.get("/api/comments", params={"notice_id": notice})
    ids = [c["id"] for c in rl.json()["items"]]
    assert cid not in ids


def test_cannot_delete_others_comment(client, student_user, notice):
    import uuid
    token_a, _ = student_user
    # 注册第二个学生（独立账号，区别于 fixture 里的学生 A）
    username_b = f"stu_b_{uuid.uuid4().hex[:10]}"
    rb = client.post("/api/auth/register", json={
        "username": username_b, "password": "pass123",
    })
    assert rb.status_code == 200
    token_b = rb.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    r = client.post("/api/comments", json={
        "notice_id": notice, "content": "B发的评论",
    }, headers=headers_b)
    cid = r.json()["id"]
    # A 试图删除 B 的评论，应 403
    headers_a = {"Authorization": f"Bearer {token_a}"}
    dr = client.delete(f"/api/comments/{cid}", headers=headers_a)
    assert dr.status_code == 403


def test_admin_can_delete_any_comment(client, admin_headers, student_user, notice):
    token_stu, _ = student_user
    headers_stu = {"Authorization": f"Bearer {token_stu}"}
    r = client.post("/api/comments", json={
        "notice_id": notice, "content": "学生评论",
    }, headers=headers_stu)
    cid = r.json()["id"]
    # 管理员删除别人评论
    dr = client.delete(f"/api/comments/{cid}", headers=admin_headers)
    assert dr.status_code == 204