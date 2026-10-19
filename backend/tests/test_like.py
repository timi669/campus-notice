# -*- coding: utf-8 -*-
"""点赞模块测试：toggle、计数、权限、详情返回。"""


def test_like_requires_login(client, notice):
    r = client.post(f"/api/notices/{notice}/like")
    assert r.status_code == 401


def test_toggle_like(client, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    nid = notice
    # 点赞
    r1 = client.post(f"/api/notices/{nid}/like", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["liked"] is True
    assert r1.json()["like_count"] == 1
    # 再点 = 取消
    r2 = client.post(f"/api/notices/{nid}/like", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["liked"] is False
    assert r2.json()["like_count"] == 0


def test_like_reflected_in_detail(client, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    nid = notice
    # 初始详情 is_liked=False, like_count=0
    d0 = client.get(f"/api/notices/{nid}", headers=headers).json()
    assert d0["is_liked"] is False
    assert d0["like_count"] == 0
    # 点赞后详情应反映
    client.post(f"/api/notices/{nid}/like", headers=headers)
    d1 = client.get(f"/api/notices/{nid}", headers=headers).json()
    assert d1["is_liked"] is True
    assert d1["like_count"] == 1


def test_multiple_users_like_count(client, student_user, notice):
    import uuid
    token_a, _ = student_user
    headers_a = {"Authorization": f"Bearer {token_a}"}
    nid = notice
    # 学生 A 点赞
    client.post(f"/api/notices/{nid}/like", headers=headers_a)
    # 注册学生 B 并点赞
    username_b = f"like_b_{uuid.uuid4().hex[:10]}"
    rb = client.post("/api/auth/register", json={"username": username_b, "password": "pass123"})
    token_b = rb.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.post(f"/api/notices/{nid}/like", headers=headers_b)
    # 列表 like_count 应为 2
    r = client.get("/api/notices", params={"page": 1, "page_size": 100})
    target = [it for it in r.json()["items"] if it["id"] == nid]
    assert len(target) == 1
    assert target[0]["like_count"] == 2


def test_like_missing_notice(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/notices/999999/like", headers=headers)
    assert r.status_code == 404