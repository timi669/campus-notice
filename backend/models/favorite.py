# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Favorite(Base):
    __tablename__ = "favorite"

    id = Column(Integer, primary_key=True, index=True, comment="收藏ID")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="用户ID")
    notice_id = Column(Integer, ForeignKey("notice.id"), nullable=False, index=True, comment="公告ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="收藏时间")

    __table_args__ = (
        UniqueConstraint("user_id", "notice_id", name="uk_user_notice"),
    )

    user = relationship("User", back_populates="favorites")
    notice = relationship("Notice", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, notice_id={self.notice_id})>"
