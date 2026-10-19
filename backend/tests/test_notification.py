# -*- coding: utf-8 -*-
"""站内通知模块测试：发布公告自动推送通知、未读数、标记已读。"""


def test_publish_notice_pushes_notification(client, admin_headers, category, db_session):
    import uuid
    from models.user import User
    from models.notification import Notification
    # 注册一个学生（接收通知的目标用户）
    username = f"noti_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={"username": username, "password": "pass123"})
    uid = r.json()["user"]["id"]
    # 管理员发公告
    r = client.post("/api/notices", json={
        "title": "推送测试公告",
        "content": "正文内容",
        "category_id": category,
        "status": 1,
    }, headers=admin_headers)
    nid = r.json()["id"]
    # 该学生应收到一条 notice 类型通知
    notifs = db_session.query(Notification).filter(
        Notification.user_id == uid,
        Notification.notice_id == nid,
    ).all()
    assert len(notifs) == 1
    assert notifs[0].type == "notice"
    assert notifs[0].is_read == 0
    # 清理
    client.delete(f"/api/notices/{nid}", headers=admin_headers)
    u = db_session.query(User).filter(User.id == uid).first()
    if u:
        db_session.delete(u)
        db_session.commit()


def test_unread_count_and_mark_read(client, admin_headers, category, student_user):
    token, uid = student_user
    headers = {"Authorization": f"Bearer {token}"}
    # 管理员发公告 -> 学生收到通知
    r = client.post("/api/notices", json={
        "title": "红点测试公告",
        "content": "正文",
        "category_id": category,
        "status": 1,
    }, headers=admin_headers)
    nid = r.json()["id"]
    # 未读数应 >= 1
    rc = client.get("/api/notifications/unread-count", headers=headers)
    assert rc.status_code == 200
    assert rc.json()["unread_count"] >= 1
    # 取通知列表取 id
    rl = client.get("/api/notifications", headers=headers)
    items = rl.json()["items"]
    target = [i for i in items if i["notice_id"] == nid]
    assert len(target) == 1
    notif_id = target[0]["id"]
    # 标记已读
    rm = client.put(f"/api/notifications/{notif_id}/read", headers=headers)
    assert rm.status_code == 200
    assert rm.json()["is_read"] == 1
    # 清理
    client.delete(f"/api/notices/{nid}", headers=admin_headers)


def test_notifications_require_login(client):
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/notifications/unread-count").status_code == 401