# -*- coding: utf-8 -*-
import csv
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload, aliased

from database import get_db
from config import settings
from models.user import User
from models.notice import Notice
from models.category import Category
from models.favorite import Favorite
from models.notice_like import NoticeLike
from models.notification import Notification
from models.search_log import SearchLog
from schemas.notice import (
    NoticeCreate,
    NoticeUpdate,
    NoticeResponse,
    NoticeListItem,
    PaginatedNoticeResponse,
)
from schemas.favorite import FavoriteToggleResponse
from schemas.like import LikeToggleResponse
from utils.auth import get_current_user, require_admin, get_optional_current_user
from utils import cache as cache_util
from utils.operation_log import log_operation

router = APIRouter(prefix="/api/notices", tags=["公告"])

CACHE_KEY_TOP = "notice:top"
CACHE_TTL_TOP = 300  # 5分钟

# 全文检索是否可用（启动时检测）
FULLTEXT_AVAILABLE = False


def check_fulltext_available(db: Session) -> bool:
    """检测 notice 表是否存在 FULLTEXT 索引"""
    global FULLTEXT_AVAILABLE
    try:
        from sqlalchemy import text
        # 查询 notice 表是否存在 FULLTEXT 索引
        result = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = 'notice' "
            "AND index_type = 'FULLTEXT'"
        )).first()
        FULLTEXT_AVAILABLE = result[0] > 0 if result else False
    except Exception:
        FULLTEXT_AVAILABLE = False
    if FULLTEXT_AVAILABLE:
        print("[Search] 全文检索 (FULLTEXT) 已启用")
    else:
        print("[Search] 未检测到 FULLTEXT 索引，搜索降级为 LIKE 模式（建议执行 sql/init.sql）")
    return FULLTEXT_AVAILABLE


def _invalidate_notice_cache():
    cache_util.delete_pattern(CACHE_KEY_TOP + "*")
    cache_util.delete("stats:overview")


def _attach_favorite_status(db: Session, user_id: Optional[int], notices: List):
    if not user_id or not notices:
        for n in notices:
            n.is_favorited = False
        return
    ids = [n.id for n in notices]
    favorited_ids = set(
        r[0] for r in db.query(Favorite.notice_id)
        .filter(Favorite.user_id == user_id, Favorite.notice_id.in_(ids))
        .all()
    )
    for n in notices:
        n.is_favorited = n.id in favorited_ids


def _attach_like_counts(db: Session, notices: List):
    if not notices:
        return
    ids = [n.id for n in notices]
    rows = (
        db.query(NoticeLike.notice_id, func.count(NoticeLike.id))
        .filter(NoticeLike.notice_id.in_(ids))
        .group_by(NoticeLike.notice_id)
        .all()
    )
    counts = {nid: cnt for nid, cnt in rows}
    for n in notices:
        n.like_count = counts.get(n.id, 0)


def _build_list_query(db: Session, category_id=None, keyword=None, status=None, author_id=None):
    query = db.query(Notice).options(joinedload(Notice.category))
    if category_id:
        query = query.filter(Notice.category_id == category_id)
    if author_id:
        query = query.filter(Notice.author_id == author_id)
    if status is not None:
        query = query.filter(Notice.status == status)
    else:
        query = query.filter(Notice.status == 1)
    if keyword:
        if FULLTEXT_AVAILABLE:
            from sqlalchemy import text
            query = query.filter(
                text("MATCH(title, content) AGAINST(:kw IN BOOLEAN MODE)")
            ).params(kw=keyword)
        else:
            like = f"%{keyword}%"
            query = query.filter(
                or_(Notice.title.like(like), Notice.content.like(like), Notice.summary.like(like))
            )
    return query


@router.get("", response_model=PaginatedNoticeResponse, summary="公告列表（分页）")
def list_notices(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    category_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    sort: str = Query("latest", description="latest / hottest"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None

    # 记录搜索日志（仅当有关键词且非空）
    if keyword and keyword.strip():
        db.add(SearchLog(keyword=keyword.strip(), user_id=user_id))
        db.commit()

    total = _build_list_query(db, category_id, keyword).count()

    query = _build_list_query(db, category_id, keyword)
    if sort == "hottest":
        query = query.order_by(desc(Notice.views_count), desc(Notice.is_top), desc(Notice.created_at))
    else:
        query = query.order_by(desc(Notice.is_top), desc(Notice.created_at))

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    from sqlalchemy.orm import make_transient
    plain_items = []
    for n in items:
        li = NoticeListItem(
            id=n.id,
            title=n.title,
            summary=n.summary,
            category_id=n.category_id,
            category=n.category,
            cover_image=n.cover_image,
            views_count=n.views_count,
            is_top=n.is_top,
            created_at=n.created_at,
            is_favorited=False,
        )
        plain_items.append(li)
    _attach_favorite_status(db, user_id, plain_items)
    _attach_like_counts(db, plain_items)

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedNoticeResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=plain_items,
    )


@router.get("/top", response_model=List[NoticeListItem], summary="置顶公告")
def top_notices(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    cache_key = f"{CACHE_KEY_TOP}:{limit}"
    cached = cache_util.get(cache_key)
    if cached is not None:
        return [NoticeListItem(**item) for item in cached]

    items = (
        db.query(Notice)
        .options(joinedload(Notice.category))
        .filter(Notice.is_top == 1, Notice.status == 1)
        .order_by(desc(Notice.created_at))
        .limit(limit)
        .all()
    )
    result = [
        NoticeListItem(
            id=n.id,
            title=n.title,
            summary=n.summary,
            category_id=n.category_id,
            category=n.category,
            cover_image=n.cover_image,
            views_count=n.views_count,
            is_top=n.is_top,
            created_at=n.created_at,
            is_favorited=False,
        )
        for n in items
    ]
    _attach_like_counts(db, result)
    cache_util.set(cache_key, [r.model_dump(mode="json") for r in result], CACHE_TTL_TOP)
    return result


@router.get("/hot-keywords", summary="热门搜索词")
def hot_keywords(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db),
):
    """统计搜索日志中出现频率最高的关键词"""
    rows = (
        db.query(SearchLog.keyword, func.count(SearchLog.id).label("cnt"))
        .group_by(SearchLog.keyword)
        .order_by(desc("cnt"))
        .limit(limit)
        .all()
    )
    return [r.keyword for r in rows]


@router.get("/export.csv", summary="导出公告列表 CSV（管理员）")
def export_notices(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """导出所有公告为 CSV 文件。

    注意：本路由必须定义在 `/{notice_id}` 之前，否则 "export.csv" 会被当作 ID 解析而报 422。
    """
    notices = (
        db.query(Notice)
        .options(joinedload(Notice.category), joinedload(Notice.author))
        .order_by(desc(Notice.created_at))
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "标题", "分类", "作者", "浏览量", "是否置顶", "状态", "创建时间"])
    for n in notices:
        writer.writerow([
            n.id,
            n.title,
            n.category.name if n.category else "",
            n.author.username if n.author else "",
            n.views_count,
            "是" if n.is_top else "否",
            "已发布" if n.status == 1 else "草稿",
            n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    output.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=notices.csv",
        "Content-Type": "text/csv; charset=utf-8",
    }

    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="export", target_type="notice", detail="导出公告列表CSV",
        ip=_get_client_ip(request),
    )

    return StreamingResponse(iter([output.getvalue()]), headers=headers)


@router.get("/{notice_id}", response_model=NoticeResponse, summary="公告详情")
def get_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None

    notice = (
        db.query(Notice)
        .options(joinedload(Notice.category), joinedload(Notice.author))
        .filter(Notice.id == notice_id)
        .first()
    )
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    if notice.status != 1:
        # 草稿仅作者本人可查看
        if not current_user or current_user.id != notice.author_id:
            raise HTTPException(status_code=404, detail="公告不存在或未发布")

    # 原子更新浏览量，避免并发竞态
    db.query(Notice).filter(Notice.id == notice_id).update(
        {Notice.views_count: Notice.views_count + 1}
    )
    db.commit()
    db.refresh(notice)

    favorited = False
    if user_id:
        favorited = (
            db.query(Favorite)
            .filter(Favorite.user_id == user_id, Favorite.notice_id == notice_id)
            .first() is not None
        )

    liked = False
    if user_id:
        liked = (
            db.query(NoticeLike)
            .filter(NoticeLike.user_id == user_id, NoticeLike.notice_id == notice_id)
            .first() is not None
        )
    like_count = db.query(NoticeLike).filter(NoticeLike.notice_id == notice_id).count()

    resp = NoticeResponse.model_validate(notice)
    resp.is_favorited = favorited
    resp.is_liked = liked
    resp.like_count = like_count
    return resp


@router.post("", response_model=NoticeResponse, summary="发布公告（管理员）")
def create_notice(
    notice_in: NoticeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == notice_in.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="分类不存在")

    notice = Notice(
        title=notice_in.title,
        content=notice_in.content,
        summary=notice_in.summary,
        category_id=notice_in.category_id,
        author_id=current_user.id,
        cover_image=notice_in.cover_image,
        is_top=notice_in.is_top,
        status=notice_in.status,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    notice.author
    notice.category

    # 发布状态的公告：给所有用户推送站内通知
    if notice.status == 1:
        _send_notice_notification(db, notice)

    _invalidate_notice_cache()

    # 记录操作日志
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="create", target_type="notice", target_id=notice.id,
        detail=f"发布公告: {notice.title[:50]}",
        ip=_get_client_ip(request),
    )

    return NoticeResponse.model_validate(notice)


def _send_notice_notification(db: Session, notice: Notice):
    """发布公告时，给所有用户创建站内通知（排除作者本人）"""
    all_user_ids = [
        uid for (uid,) in db.query(User.id).filter(User.id != notice.author_id).all()
    ]
    if not all_user_ids:
        return
    notifications = [
        Notification(
            user_id=uid,
            title=notice.title,
            content=notice.summary or (notice.content[:100] + "..." if notice.content else None),
            notice_id=notice.id,
            type="notice",
            is_read=0,
        )
        for uid in all_user_ids
    ]
    db.bulk_save_objects(notifications)
    db.commit()


@router.put("/{notice_id}", response_model=NoticeResponse, summary="更新公告（管理员）")
def update_notice(
    notice_id: int,
    notice_in: NoticeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    old_status = notice.status
    old_title = notice.title
    update_data = notice_in.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        cat = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")
    for k, v in update_data.items():
        setattr(notice, k, v)
    db.commit()
    db.refresh(notice)
    notice.author
    notice.category

    # 草稿转为发布时，给所有用户推送通知
    if old_status == 0 and notice.status == 1:
        _send_notice_notification(db, notice)

    _invalidate_notice_cache()

    # 记录操作日志
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="update", target_type="notice", target_id=notice.id,
        detail=f"编辑公告: {old_title[:50]}",
        ip=_get_client_ip(request),
    )

    return NoticeResponse.model_validate(notice)


@router.delete("/{notice_id}", status_code=204, summary="删除公告（管理员）")
def delete_notice(
    notice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    title = notice.title
    db.delete(notice)
    db.commit()
    _invalidate_notice_cache()

    # 记录操作日志
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="delete", target_type="notice", target_id=notice_id,
        detail=f"删除公告: {title[:50]}",
        ip=_get_client_ip(request),
    )


@router.post("/{notice_id}/favorite", response_model=FavoriteToggleResponse, summary="收藏/取消收藏公告")
def toggle_favorite(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id, Notice.status == 1).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")

    fav = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.notice_id == notice_id).first()
    if fav:
        db.delete(fav)
        db.commit()
        return FavoriteToggleResponse(favorited=False, favorite_id=None)
    fav = Favorite(user_id=current_user.id, notice_id=notice_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return FavoriteToggleResponse(favorited=True, favorite_id=fav.id)


@router.post("/{notice_id}/like", response_model=LikeToggleResponse, summary="点赞/取消点赞公告")
def toggle_like(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id, Notice.status == 1).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")

    like = db.query(NoticeLike).filter(
        NoticeLike.user_id == current_user.id, NoticeLike.notice_id == notice_id
    ).first()
    if like:
        db.delete(like)
        db.commit()
        _invalidate_notice_cache()
        like_count = db.query(NoticeLike).filter(NoticeLike.notice_id == notice_id).count()
        return LikeToggleResponse(liked=False, liked_id=None, like_count=like_count)
    like = NoticeLike(user_id=current_user.id, notice_id=notice_id)
    db.add(like)
    db.commit()
    db.refresh(like)
    _invalidate_notice_cache()
    like_count = db.query(NoticeLike).filter(NoticeLike.notice_id == notice_id).count()
    return LikeToggleResponse(liked=True, liked_id=like.id, like_count=like_count)


@router.get("/my/favorites", response_model=PaginatedNoticeResponse, summary="我的收藏")
def my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = db.query(Favorite).filter(Favorite.user_id == current_user.id)
    total = base.count()
    favs = base.order_by(desc(Favorite.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    notice_ids = [f.notice_id for f in favs]
    notices = []
    if notice_ids:
        rows = (
            db.query(Notice)
            .options(joinedload(Notice.category))
            .filter(Notice.id.in_(notice_ids), Notice.status == 1)
            .all()
        )
        id_map = {n.id: n for n in rows}
        for fid in notice_ids:
            if fid in id_map:
                n = id_map[fid]
                notices.append(
                    NoticeListItem(
                        id=n.id,
                        title=n.title,
                        summary=n.summary,
                        category_id=n.category_id,
                        category=n.category,
                        cover_image=n.cover_image,
                        views_count=n.views_count,
                        is_top=n.is_top,
                        created_at=n.created_at,
                        is_favorited=True,
                    )
                )
    _attach_like_counts(db, notices)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedNoticeResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=notices,
    )


@router.get("/my/published", response_model=PaginatedNoticeResponse, summary="我发布的公告（管理员）")
def my_published(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total = db.query(Notice).filter(Notice.author_id == current_user.id).count()
    rows = (
        db.query(Notice)
        .options(joinedload(Notice.category))
        .filter(Notice.author_id == current_user.id)
        .order_by(desc(Notice.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        NoticeListItem(
            id=n.id,
            title=n.title,
            summary=n.summary,
            category_id=n.category_id,
            category=n.category,
            cover_image=n.cover_image,
            views_count=n.views_count,
            is_top=n.is_top,
            created_at=n.created_at,
            is_favorited=False,
        )
        for n in rows
    ]
    _attach_favorite_status(db, current_user.id, items)
    _attach_like_counts(db, items)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedNoticeResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP，优先读取反向代理转发的 X-Forwarded-For"""
    if not request:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
