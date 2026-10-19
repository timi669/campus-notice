# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Comment(Base):
    """公告评论表"""
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True, index=True, comment="评论ID")
    notice_id = Column(Integer, ForeignKey("notice.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联公告ID")
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True, comment="评论用户ID")
    content = Column(Text, nullable=False, comment="评论内容")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="评论时间")

    notice = relationship("Notice")
    user = relationship("User")

    def __repr__(self):
        return f"<Comment(id={self.id}, notice_id={self.notice_id}, user_id={self.user_id})>"