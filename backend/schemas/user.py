# -*- coding: utf-8 -*-
from typing import Optional
from datetime import datetime
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator


def validate_password_strength(password: str) -> str:
    """密码强度校验：6-50位，必须包含字母和数字"""
    if len(password) < 6 or len(password) > 50:
        raise ValueError("密码长度须为6-50位")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("密码必须包含字母")
    if not re.search(r"\d", password):
        raise ValueError("密码必须包含数字")
    return password


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")


class UserCreate(UserBase):
    password: str = Field(..., description="密码（6-50位，须包含字母和数字）")

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=255)


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., description="新密码（6-50位，须包含字母和数字）")

    @field_validator("new_password")
    @classmethod
    def _check_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


class RoleUpdate(BaseModel):
    role: str = Field(..., description="角色: student/admin")


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    created_at: datetime
    updated_at: datetime


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: Optional[str]
    avatar: Optional[str]
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
