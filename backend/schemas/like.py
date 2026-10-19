# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel, Field


class LikeToggleResponse(BaseModel):
    liked: bool
    liked_id: Optional[int] = None
    like_count: int = 0