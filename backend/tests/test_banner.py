# -*- coding: utf-8 -*-
"""轮播图模块测试：CRUD、权限、公开列表。"""


def test_banner_list_public(client):
    """公开接口：默认只返回启用项。"""
    r = client.get("/api/banners")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_banner_requires_admin(client, student_user):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/banners", json={"image": "/uploads/x.png"}, headers=headers)
    assert r.status_code == 403


def test_create_banner_requires_login(client):
    r = client.post("/api/banners", json={"image": "/uploads/x.png"})
    assert r.status_code == 401


def test_banner_crud(client, admin_headers):
    # 创建
    r = client.post("/api/banners", json={
        "image": "/uploads/banner1.png",
        "title": "国庆活动",
        "link_type": "notice",
        "link_value": "1",
        "sort_order": 1,
        "status": 1,
    }, headers=admin_headers)
    assert r.status_code == 200, f"创建失败: {r.text}"
    bid = r.json()["id"]
    assert r.json()["title"] == "国庆活动"

    # 公开列表能看到（启用的）
    rl = client.get("/api/banners")
    ids = [b["id"] for b in rl.json()]
    assert bid in ids

    # 更新
    ru = client.put(f"/api/banners/{bid}", json={"title": "国庆活动-改", "sort_order": 5}, headers=admin_headers)
    assert ru.status_code == 200
    assert ru.json()["title"] == "国庆活动-改"
    assert ru.json()["sort_order"] == 5

    # 禁用后公开列表看不到
    client.put(f"/api/banners/{bid}", json={"status": 0}, headers=admin_headers)
    rl2 = client.get("/api/banners")
    ids2 = [b["id"] for b in rl2.json()]
    assert bid not in ids2
    # 但 include_disabled=true 能看到
    rl3 = client.get("/api/banners", params={"include_disabled": True})
    ids3 = [b["id"] for b in rl3.json()]
    assert bid in ids3

    # 删除
    dr = client.delete(f"/api/banners/{bid}", headers=admin_headers)
    assert dr.status_code == 204
    assert client.get("/api/banners", params={"include_disabled": True}).json() == [] or bid not in [b["id"] for b in client.get("/api/banners", params={"include_disabled": True}).json()]


def test_banner_update_not_found(client, admin_headers):
    r = client.put("/api/banners/999999", json={"title": "x"}, headers=admin_headers)
    assert r.status_code == 404


def test_banner_delete_not_found(client, admin_headers):
    r = client.delete("/api/banners/999999", headers=admin_headers)
    assert r.status_code == 404