# -*- coding: utf-8 -*-
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(0, description="响应码，0表示成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class PaginatedParams(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页条数")
