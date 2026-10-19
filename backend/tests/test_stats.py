# -*- coding: utf-8 -*-
"""统计接口测试：评论数、点赞数、收藏数。"""


def test_stats_requires_admin(client):
    assert client.get("/api/stats").status_code == 401


def test_stats_has_comment_and_like_counts(client, admin_headers):
    r = client.get("/api/stats", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "comment_count" in data
    assert "like_count" in data
    assert isinstance(data["comment_count"], int)
    assert isinstance(data["like_count"], int)


def test_stats_reflects_new_comment_and_like(client, admin_headers, student_user, notice):
    token, _ = student_user
    headers = {"Authorization": f"Bearer {token}"}

    # 新增评论 + 点赞
    rc = client.post("/api/comments", json={
        "notice_id": notice, "content": "统计测试评论",
    }, headers=headers)
    assert rc.status_code == 200
    rl = client.post(f"/api/notices/{notice}/like", headers=headers)
    assert rl.status_code == 200

    # 确保读到最新数据（评论/点赞已触发统计缓存失效）
    r = client.get("/api/stats", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["comment_count"] >= 1
    assert data["like_count"] >= 1