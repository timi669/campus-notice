# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: Optional[str] = None
    notice_id: Optional[int] = None
    type: str
    is_read: int
    created_at: datetime


class NotificationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[NotificationResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int
