# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class OperationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip: Optional[str] = None
    created_at: datetime


class OperationLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[OperationLogResponse]
