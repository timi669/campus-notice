# -*- coding: utf-8 -*-
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    notice_id: int
    created_at: datetime


class FavoriteToggleResponse(BaseModel):
    favorited: bool
    favorite_id: Optional[int] = None
