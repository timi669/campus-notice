# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Notice(Base):
    __tablename__ = "notice"

    id = Column(Integer, primary_key=True, index=True, comment="公告ID")
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容")
    summary = Column(String(500), default=None, comment="摘要")
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, index=True, comment="分类ID")
    author_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="发布者ID")
    cover_image = Column(String(255), default=None, comment="封面图URL")
    views_count = Column(Integer, nullable=False, default=0, comment="浏览次数")
    is_top = Column(SmallInteger, nullable=False, default=0, index=True, comment="是否置顶: 1-是, 0-否")
    status = Column(SmallInteger, nullable=False, default=1, index=True, comment="状态: 1-发布, 0-草稿")
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    category = relationship("Category", back_populates="notices")
    author = relationship("User", back_populates="notices")
    favorites = relationship("Favorite", back_populates="notice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Notice(id={self.id}, title={self.title[:30]})>"
