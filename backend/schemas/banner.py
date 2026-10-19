# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BannerCreate(BaseModel):
    image: str = Field(..., max_length=255, description="图片URL")
    title: Optional[str] = Field(None, max_length=200, description="标题")
    link_type: str = Field("notice", description="跳转类型: notice/none/url")
    link_value: Optional[str] = Field(None, max_length=255, description="跳转目标（公告ID或外链URL）")
    sort_order: int = Field(0, ge=0, description="排序值")
    status: int = Field(1, ge=0, le=1, description="状态: 1-启用 0-禁用")


class BannerUpdate(BaseModel):
    image: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=200)
    link_type: Optional[str] = Field(None)
    link_value: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=0, le=1)


class BannerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image: str
    title: Optional[str] = None
    link_type: str
    link_value: Optional[str] = None
    sort_order: int
    status: int
    created_at: datetime
    updated_at: datetime