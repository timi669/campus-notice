# -*- coding: utf-8 -*-
"""公告模块测试：CRUD、列表/详情、收藏、浏览量自增。"""


def test_create_notice_as_admin(client, admin_headers, category):
    r = client.post("/api/notices", json={
        "title": "国庆放假通知",
        "content": "10月1日至7日放假。",
        "summary": "放假7天",
        "category_id": category,
        "is_top": 1,
        "status": 1,
    }, headers=admin_headers)
    assert r.status_code == 200, f"发布公告应成功: {r.text}"
    data = r.json()
    assert data["title"] == "国庆放假通知"
    assert data["status"] == 1
    assert data["is_top"] == 1
    assert data["views_count"] == 0
    assert data["author"]["username"] == "admin"
    nid = data["id"]
    # 清理
    client.delete(f"/api/notices/{nid}", headers=admin_headers)


def test_create_notice_requires_admin(student_user, client, category):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/notices", json={
        "title": "学生违规发布",
        "content": "正文",
        "category_id": category,
        "status": 1,
    }, headers=headers)
    assert r.status_code == 403


def test_create_notice_with_bad_category(client, admin_headers):
    r = client.post("/api/notices", json={
        "title": "错误分类",
        "content": "正文",
        "category_id": 999999,
        "status": 1,
    }, headers=admin_headers)
    assert r.status_code == 400


def test_list_notices(client):
    r = client.get("/api/notices", params={"page": 1, "page_size": 10})
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_get_notice_detail_increments_views(client, notice):
    nid = notice
    # 第一次访问
    r1 = client.get(f"/api/notices/{nid}")
    assert r1.status_code == 200
    views1 = r1.json()["views_count"]
    # 第二次访问，浏览量应 +1
    r2 = client.get(f"/api/notices/{nid}")
    assert r2.status_code == 200
    views2 = r2.json()["views_count"]
    assert views2 == views1 + 1


def test_get_notice_not_found(client):
    r = client.get("/api/notices/999999")
    assert r.status_code == 404


def test_update_notice(client, admin_headers, notice):
    nid = notice
    r = client.put(f"/api/notices/{nid}", json={
        "title": "更新后的标题",
        "is_top": 1,
    }, headers=admin_headers)
    assert r.status_code == 200, f"更新公告应成功: {r.text}"
    data = r.json()
    assert data["title"] == "更新后的标题"
    assert data["is_top"] == 1


def test_delete_notice(client, admin_headers, category):
    # 创建后立即删除
    r = client.post("/api/notices", json={
        "title": "待删除公告",
        "content": "正文",
        "category_id": category,
        "status": 1,
    }, headers=admin_headers)
    nid = r.json()["id"]
    dr = client.delete(f"/api/notices/{nid}", headers=admin_headers)
    assert dr.status_code == 204
    # 删除后详情应为 404
    assert client.get(f"/api/notices/{nid}").status_code == 404


def test_favorite_toggle(client, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    nid = notice
    # 收藏
    r1 = client.post(f"/api/notices/{nid}/favorite", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["favorited"] is True
    assert r1.json()["favorite_id"] is not None
    # 再次收藏 = 取消收藏
    r2 = client.post(f"/api/notices/{nid}/favorite", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["favorited"] is False
    assert r2.json()["favorite_id"] is None


def test_favorite_requires_login(client, notice):
    r = client.post(f"/api/notices/{notice}/favorite")
    assert r.status_code == 401


def test_my_favorites(client, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    nid = notice
    # 先收藏
    assert client.post(f"/api/notices/{nid}/favorite", headers=headers).status_code == 200
    # 查收藏列表
    r = client.get("/api/notices/my/favorites", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    ids = [it["id"] for it in data["items"]]
    assert nid in ids