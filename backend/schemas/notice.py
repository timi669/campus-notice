# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NoticeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容")
    summary: Optional[str] = Field(None, max_length=500, description="摘要")
    category_id: int = Field(..., gt=0, description="分类ID")
    cover_image: Optional[str] = Field(None, max_length=255, description="封面图URL")
    is_top: int = Field(0, ge=0, le=1, description="是否置顶: 1-是 0-否")
    status: int = Field(1, ge=0, le=1, description="状态: 1-发布 0-草稿")


class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = Field(None, gt=0)
    cover_image: Optional[str] = Field(None, max_length=255)
    is_top: Optional[int] = Field(None, ge=0, le=1)
    status: Optional[int] = Field(None, ge=0, le=1)


class _AuthorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: Optional[str]
    username: str


class _CategoryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: Optional[str]


class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    summary: Optional[str]
    category_id: int
    category: Optional[_CategoryInfo] = None
    author_id: int
    author: Optional[_AuthorInfo] = None
    cover_image: Optional[str]
    views_count: int
    is_top: int
    status: int
    is_favorited: Optional[bool] = Field(False, description="当前用户是否已收藏")
    is_liked: Optional[bool] = Field(False, description="当前用户是否已点赞")
    like_count: int = Field(0, description="点赞总数")
    created_at: datetime
    updated_at: datetime


class NoticeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: Optional[str]
    category_id: int
    category: Optional[_CategoryInfo] = None
    cover_image: Optional[str]
    views_count: int
    is_top: int
    created_at: datetime
    is_favorited: Optional[bool] = Field(False)
    like_count: int = Field(0, description="点赞总数")


class PaginatedNoticeResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[NoticeListItem]
