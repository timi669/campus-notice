# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=255, description="图标")
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    status: int = Field(1, ge=0, le=1, description="状态: 1-启用 0-禁用")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    icon: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=0, le=1)


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    notice_count: Optional[int] = Field(0, description="该分类下公告数量")
