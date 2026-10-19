# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.notice import Notice
from models.category import Category
from models.favorite import Favorite
from utils.auth import require_admin
from utils import cache as cache_util

router = APIRouter(prefix="/api/stats", tags=["统计"])

CACHE_KEY_STATS = "stats:overview"
CACHE_TTL_STATS = 60  # 1分钟


@router.get("", summary="系统概览统计（管理员）")
def overview(_=Depends(require_admin), db: Session = Depends(get_db)):
    # 尝试从缓存读取
    cached = cache_util.get(CACHE_KEY_STATS)
    if cached is not None:
        return cached

    user_count = db.query(func.count(User.id)).scalar() or 0
    admin_count = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    notice_count = db.query(func.count(Notice.id)).filter(Notice.status == 1).scalar() or 0
    draft_count = db.query(func.count(Notice.id)).filter(Notice.status == 0).scalar() or 0
    category_count = db.query(func.count(Category.id)).filter(Category.status == 1).scalar() or 0
    favorite_count = db.query(func.count(Favorite.id)).scalar() or 0
    views_sum = db.query(func.sum(Notice.views_count)).scalar() or 0

    recent_notices = (
        db.query(Notice.id, Notice.title, Notice.created_at, Notice.views_count)
        .filter(Notice.status == 1)
        .order_by(Notice.created_at.desc())
        .limit(5)
        .all()
    )
    hot_notices = (
        db.query(Notice.id, Notice.title, Notice.views_count)
        .filter(Notice.status == 1)
        .order_by(Notice.views_count.desc())
        .limit(5)
        .all()
    )
    category_stats = (
        db.query(
            Category.id,
            Category.name,
            func.count(Notice.id).label("cnt"),
        )
        .outerjoin(Notice, (Notice.category_id == Category.id) & (Notice.status == 1))
        .filter(Category.status == 1)
        .group_by(Category.id, Category.name)
        .order_by(Category.sort_order.asc())
        .all()
    )

    result = {
        "user_count": user_count,
        "admin_count": admin_count,
        "student_count": user_count - admin_count,
        "notice_count": notice_count,
        "draft_count": draft_count,
        "category_count": category_count,
        "favorite_count": favorite_count,
        "views_sum": int(views_sum),
        "recent_notices": [
            {"id": n.id, "title": n.title, "created_at": n.created_at, "views_count": n.views_count}
            for n in recent_notices
        ],
        "hot_notices": [
            {"id": n.id, "title": n.title, "views_count": n.views_count}
            for n in hot_notices
        ],
        "category_stats": [
            {"id": c.id, "name": c.name, "notice_count": c.cnt or 0}
            for c in category_stats
        ],
    }
    # 写入缓存
    cache_util.set(CACHE_KEY_STATS, result, CACHE_TTL_STATS)
    return result
