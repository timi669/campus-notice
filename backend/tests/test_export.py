# -*- coding: utf-8 -*-
"""CSV 导出接口测试（含路由顺序回归：export.csv 不能被 /{id} 吞掉）。"""


def test_export_users_requires_admin(client):
    assert client.get("/api/users/export.csv").status_code == 401


def test_export_users_csv(client, admin_headers):
    r = client.get("/api/users/export.csv", headers=admin_headers)
    assert r.status_code == 200, f"导出用户 CSV 应返回 200，实际 {r.status_code}: {r.text[:200]}"
    assert "text/csv" in r.headers["content-type"]
    # 表头包含中文列名
    assert "用户名" in r.text
    assert "ID" in r.text


def test_export_notices_csv(client, admin_headers):
    r = client.get("/api/notices/export.csv", headers=admin_headers)
    assert r.status_code == 200, f"导出公告 CSV 应返回 200，实际 {r.status_code}: {r.text[:200]}"
    assert "text/csv" in r.headers["content-type"]
    assert "标题" in r.text


def test_export_csv_route_not_matched_as_id(client, admin_headers):
    """回归测试：/api/notices/export.csv 不能被 /{notice_id} 当成 ID 解析（否则 422）。"""
    r = client.get("/api/notices/export.csv", headers=admin_headers)
    assert r.status_code == 200
    # 不应出现 FastAPI 的参数校验错误
    assert "int_parsing" not in r.text
    assert "Input should be a valid integer" not in r.text