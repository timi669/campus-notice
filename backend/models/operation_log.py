# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index

from database import Base


class OperationLog(Base):
    """操作日志表 - 记录管理员的关键操作"""
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    user_id = Column(Integer, nullable=False, index=True, comment="操作用户ID")
    username = Column(String(50), nullable=False, comment="操作用户名")
    action = Column(String(50), nullable=False, index=True, comment="操作类型: create/update/delete/login等")
    target_type = Column(String(50), default=None, comment="操作对象类型: notice/user/category等")
    target_id = Column(Integer, default=None, comment="操作对象ID")
    detail = Column(Text, default=None, comment="操作详情(变更内容摘要)")
    ip = Column(String(50), default=None, comment="操作IP")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")

    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
        Index("idx_action_time", "action", "created_at"),
    )

    def __repr__(self):
        return f"<OperationLog(id={self.id}, user={self.username}, action={self.action})>"
