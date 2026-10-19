# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class NoticeLike(Base):
    """公告点赞表"""
    __tablename__ = "notice_like"

    id = Column(Integer, primary_key=True, index=True, comment="点赞ID")
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True, comment="点赞用户ID")
    notice_id = Column(Integer, ForeignKey("notice.id", ondelete="CASCADE"), nullable=False, index=True, comment="公告ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="点赞时间")

    __table_args__ = (
        UniqueConstraint("user_id", "notice_id", name="uk_user_notice_like"),
    )

    user = relationship("User")
    notice = relationship("Notice")

    def __repr__(self):
        return f"<NoticeLike(id={self.id}, user_id={self.user_id}, notice_id={self.notice_id})>"