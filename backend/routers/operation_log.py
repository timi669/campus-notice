# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from models.user import User
from models.operation_log import OperationLog
from schemas.operation_log import OperationLogListResponse, OperationLogResponse
from utils.auth import require_admin

router = APIRouter(prefix="/api/operation-logs", tags=["操作日志"])


@router.get("", response_model=OperationLogListResponse, summary="操作日志列表（管理员）")
def list_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    user_id: Optional[int] = Query(None, description="按操作用户过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    target_type: Optional[str] = Query(None, description="按操作对象类型过滤"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(OperationLog)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if action:
        query = query.filter(OperationLog.action == action)
    if target_type:
        query = query.filter(OperationLog.target_type == target_type)

    total = query.count()
    items = (
        query.order_by(desc(OperationLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return OperationLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[OperationLogResponse.model_validate(i) for i in items],
    )
