# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger
from sqlalchemy.orm import relationship

from database import Base


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True, comment="分类ID")
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(255), default=None, comment="分类图标")
    sort_order = Column(Integer, nullable=False, default=0, index=True, comment="排序值，越小越靠前")
    status = Column(SmallInteger, nullable=False, default=1, index=True, comment="状态: 1-启用, 0-禁用")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    notices = relationship("Notice", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"
