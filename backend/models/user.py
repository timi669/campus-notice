# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"
VALID_ROLES = (ROLE_STUDENT, ROLE_ADMIN)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码(哈希)")
    nickname = Column(String(50), default=None, comment="昵称")
    avatar = Column(String(255), default=None, comment="头像URL")
    role = Column(String(20), nullable=False, default=ROLE_STUDENT, index=True, comment="角色: student/admin")
    openid = Column(String(100), default=None, comment="微信openid")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    notices = relationship("Notice", back_populates="author", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
