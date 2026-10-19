# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger

from database import Base


class Banner(Base):
    """首页轮播图表"""
    __tablename__ = "banner"

    id = Column(Integer, primary_key=True, index=True, comment="轮播图ID")
    image = Column(String(255), nullable=False, comment="图片URL")
    title = Column(String(200), default=None, comment="标题")
    link_type = Column(String(20), nullable=False, default="notice", comment="跳转类型: notice-公告 / none-无跳转 / url-外链")
    link_value = Column(String(255), default=None, comment="跳转目标（公告ID或外链URL）")
    sort_order = Column(Integer, nullable=False, default=0, index=True, comment="排序值，越小越靠前")
    status = Column(SmallInteger, nullable=False, default=1, index=True, comment="状态: 1-启用, 0-禁用")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<Banner(id={self.id}, title={self.title})>"