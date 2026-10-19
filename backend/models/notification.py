# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, SmallInteger, Index
from sqlalchemy.orm import relationship

from database import Base


class Notification(Base):
    __tablename__ = "notification"

    id = Column(Integer, primary_key=True, index=True, comment="通知ID")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="接收用户ID")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, default=None, comment="通知内容")
    notice_id = Column(Integer, ForeignKey("notice.id", ondelete="SET NULL"), default=None, index=True, comment="关联公告ID")
    type = Column(String(20), nullable=False, default="system", comment="通知类型: system/notice")
    is_read = Column(SmallInteger, nullable=False, default=0, index=True, comment="是否已读: 1-是 0-否")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_user_read", "user_id", "is_read"),
    )

    user = relationship("User", back_populates="notifications")
    notice = relationship("Notice")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title={self.title[:20]})>"
