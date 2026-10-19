# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommentCreate(BaseModel):
    notice_id: int = Field(..., gt=0, description="公告ID")
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")


class _CommentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notice_id: int
    user_id: int
    user: Optional[_CommentUser] = None
    content: str
    created_at: datetime


class CommentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CommentResponse]