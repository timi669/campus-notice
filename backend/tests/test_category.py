# -*- coding: utf-8 -*-
"""分类模块测试。"""


def test_list_categories_public(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_category_requires_admin(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/categories", json={"name": "无权限分类"}, headers=headers)
    assert r.status_code == 403


def test_create_category(client, admin_headers):
    r = client.post("/api/categories", json={
        "name": "新建分类", "icon": "📌", "sort_order": 1,
    }, headers=admin_headers)
    assert r.status_code == 200, f"创建分类失败: {r.text}"
    cid = r.json()["id"]
    assert r.json()["name"] == "新建分类"
    # 清理
    client.delete(f"/api/categories/{cid}", headers=admin_headers)


def test_update_category(client, admin_headers, category):
    r = client.put(f"/api/categories/{category}", json={"name": "改名分类"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "改名分类"


def test_delete_category_with_notice_blocked(client, admin_headers, notice, category):
    """分类下有公告时不能删除。"""
    r = client.delete(f"/api/categories/{category}", headers=admin_headers)
    assert r.status_code == 400
    assert "无法删除" in r.json()["detail"]


def test_delete_empty_category(client, admin_headers):
    r = client.post("/api/categories", json={"name": "待删分类"}, headers=admin_headers)
    cid = r.json()["id"]
    dr = client.delete(f"/api/categories/{cid}", headers=admin_headers)
    assert dr.status_code == 204