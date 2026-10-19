# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc

from database import get_db
from models.user import User
from models.banner import Banner
from schemas.banner import BannerCreate, BannerUpdate, BannerResponse
from utils.auth import require_admin
from utils import cache as cache_util
from utils.operation_log import log_operation

router = APIRouter(prefix="/api/banners", tags=["轮播图"])

CACHE_KEY_BANNERS = "banner:list"
CACHE_TTL_BANNERS = 300  # 5 分钟


def _invalidate_banner_cache():
    # 缓存 key 形如 banner:list:True / banner:list:False，按前缀统一清除
    cache_util.delete_pattern(CACHE_KEY_BANNERS + "*")


@router.get("", response_model=List[BannerResponse], summary="轮播图列表（仅启用）")
def list_banners(
    include_disabled: bool = Query(False, description="是否包含禁用项（管理员可传 true）"),
    db: Session = Depends(get_db),
):
    """公开接口：默认只返回启用中的轮播图。"""
    cache_key = f"{CACHE_KEY_BANNERS}:{include_disabled}"
    cached = cache_util.get(cache_key)
    if cached is not None:
        return [BannerResponse(**item) for item in cached]

    query = db.query(Banner)
    if not include_disabled:
        query = query.filter(Banner.status == 1)
    banners = query.order_by(asc(Banner.sort_order), asc(Banner.id)).all()
    result = [BannerResponse.model_validate(b) for b in banners]
    cache_util.set(cache_key, [r.model_dump(mode="json") for r in result], CACHE_TTL_BANNERS)
    return result


@router.post("", response_model=BannerResponse, summary="新建轮播图（管理员）")
def create_banner(
    banner_in: BannerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = Banner(**banner_in.model_dump())
    db.add(banner)
    db.commit()
    db.refresh(banner)
    _invalidate_banner_cache()
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="create", target_type="banner", target_id=banner.id,
        detail=f"新建轮播图: {banner.title or banner.image}",
    )
    return BannerResponse.model_validate(banner)


@router.put("/{banner_id}", response_model=BannerResponse, summary="更新轮播图（管理员）")
def update_banner(
    banner_id: int,
    banner_in: BannerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    update_data = banner_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(banner, k, v)
    db.commit()
    db.refresh(banner)
    _invalidate_banner_cache()
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="update", target_type="banner", target_id=banner_id,
        detail=f"更新轮播图: {banner.title or banner.image}",
    )
    return BannerResponse.model_validate(banner)


@router.delete("/{banner_id}", status_code=204, summary="删除轮播图（管理员）")
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    title = banner.title or banner.image
    db.delete(banner)
    db.commit()
    _invalidate_banner_cache()
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="delete", target_type="banner", target_id=banner_id,
        detail=f"删除轮播图: {title}",
    )