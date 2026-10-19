# -*- coding: utf-8 -*-
"""操作日志模块测试：登录产生日志、发布公告产生日志、查询接口 + 权限。"""


def test_login_writes_operation_log(client, admin_token, db_session):
    from models.operation_log import OperationLog
    _ = admin_token  # 触发 admin 登录（其实在 fixture 阶段已登录）
    logs = db_session.query(OperationLog).filter(
        OperationLog.action == "login"
    ).all()
    assert len(logs) >= 1
    assert logs[0].username == "admin"


def test_create_notice_writes_operation_log(client, admin_headers, category, db_session):
    from models.operation_log import OperationLog
    r = client.post("/api/notices", json={
        "title": "日志测试公告",
        "content": "正文",
        "category_id": category,
        "status": 1,
    }, headers=admin_headers)
    nid = r.json()["id"]
    logs = db_session.query(OperationLog).filter(
        OperationLog.action == "create",
        OperationLog.target_type == "notice",
        OperationLog.target_id == nid,
    ).all()
    assert len(logs) >= 1
    assert logs[0].username == "admin"
    assert "日志测试公告" in (logs[0].detail or "")
    # 清理
    client.delete(f"/api/notices/{nid}", headers=admin_headers)


def test_list_operation_logs_requires_admin(client):
    r = client.get("/api/operation-logs")
    assert r.status_code == 401


def test_list_operation_logs(client, admin_headers):
    r = client.get("/api/operation-logs", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data


def test_list_operation_logs_filter_by_action(client, admin_headers):
    r = client.get("/api/operation-logs", params={"action": "login"}, headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["action"] == "login"