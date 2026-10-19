# -*- coding: utf-8 -*-
"""操作日志工具"""
from typing import Optional
from sqlalchemy.orm import Session

from models.operation_log import OperationLog


def log_operation(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
    ip: Optional[str] = None,
) -> None:
    """记录一条操作日志（同步写入，开销小）"""
    log = OperationLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip=ip,
    )
    db.add(log)
    db.commit()
