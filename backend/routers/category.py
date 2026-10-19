# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User
from models.category import Category
from models.notice import Notice
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from utils.auth import get_current_user, require_admin
from utils import cache as cache_util
from utils.operation_log import log_operation

router = APIRouter(prefix="/api/categories", tags=["分类"])

CACHE_KEY_CATEGORY = "category:list"
CACHE_TTL_CATEGORY = 600  # 10分钟


def _invalidate_category_cache():
    cache_util.delete_pattern(CACHE_KEY_CATEGORY + "*")


@router.get("", response_model=List[CategoryResponse], summary="获取分类列表")
def list_categories(
    include_disabled: bool = Query(False, description="是否包含禁用分类"),
    db: Session = Depends(get_db),
):
    cache_key = f"{CACHE_KEY_CATEGORY}:{include_disabled}"
    cached = cache_util.get(cache_key)
    if cached is not None:
        return [CategoryResponse(**item) for item in cached]

    query = db.query(Category)
    if not include_disabled:
        query = query.filter(Category.status == 1)

    categories = query.order_by(Category.sort_order.asc(), Category.id.asc()).all()

    category_ids = [c.id for c in categories]
    counts = {}
    if category_ids:
        rows = (
            db.query(Notice.category_id, func.count(Notice.id))
            .filter(Notice.status == 1, Notice.category_id.in_(category_ids))
            .group_by(Notice.category_id)
            .all()
        )
        counts = {cid: cnt for cid, cnt in rows}

    result = []
    for cat in categories:
        resp = CategoryResponse.model_validate(cat)
        resp.notice_count = counts.get(cat.id, 0)
        result.append(resp)

    # 写入缓存
    cache_util.set(cache_key, [r.model_dump(mode="json") for r in result], CACHE_TTL_CATEGORY)
    return result


@router.get("/{category_id}", response_model=CategoryResponse, summary="获取分类详情")
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return CategoryResponse.model_validate(category)


@router.post("", response_model=CategoryResponse, summary="创建分类（管理员）")
def create_category(
    cat_in: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = Category(**cat_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    _invalidate_category_cache()

    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="create", target_type="category", target_id=category.id,
        detail=f"创建分类: {category.name}",
        ip=_get_client_ip(request),
    )

    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse, summary="更新分类（管理员）")
def update_category(
    category_id: int,
    cat_in: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    update_data = cat_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(category, k, v)
    db.commit()
    db.refresh(category)
    _invalidate_category_cache()

    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="update", target_type="category", target_id=category_id,
        detail=f"编辑分类: {category.name}",
        ip=_get_client_ip(request),
    )

    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=204, summary="删除分类（管理员）")
def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    notice_count = db.query(Notice).filter(Notice.category_id == category_id).count()
    if notice_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该分类下还有 {notice_count} 篇公告，无法删除",
        )
    name = category.name
    db.delete(category)
    db.commit()
    _invalidate_category_cache()

    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="delete", target_type="category", target_id=category_id,
        detail=f"删除分类: {name}",
        ip=_get_client_ip(request),
    )


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    if not request:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
