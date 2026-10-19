# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index

from database import Base


class SearchLog(Base):
    """搜索日志表 - 记录用户搜索行为，用于统计热门搜索词"""
    __tablename__ = "search_log"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    keyword = Column(String(200), nullable=False, index=True, comment="搜索关键词")
    user_id = Column(Integer, default=None, comment="搜索用户ID（未登录为NULL）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="搜索时间")

    __table_args__ = (
        Index("idx_keyword_time", "keyword", "created_at"),
    )

    def __repr__(self):
        return f"<SearchLog(id={self.id}, keyword={self.keyword})>"
