# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from models.user import User
from models.notification import Notification
from schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("", response_model=NotificationListResponse, summary="我的通知列表")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    is_read: Optional[int] = Query(None, ge=0, le=1, description="按已读状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    total = query.count()
    items = (
        query.order_by(desc(Notification.is_read), desc(Notification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return NotificationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[NotificationResponse.model_validate(n) for n in items],
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="未读通知数量")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == 0)
        .count()
    )
    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="标记单条通知已读")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")
    notif.is_read = 1
    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)


@router.put("/read-all", summary="标记全部通知已读")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == 0,
    ).update({Notification.is_read: 1}, synchronize_session=False)
    db.commit()
    return {"code": 0, "message": "已全部标记为已读"}
