# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from database import get_db
from config import settings
from models.user import User
from models.notice import Notice
from models.comment import Comment
from schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/comments", tags=["评论"])


@router.get("", response_model=CommentListResponse, summary="公告评论列表")
def list_comments(
    notice_id: int = Query(..., description="公告ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
):
    """查看某条公告的评论（公开，无需登录）。"""
    query = db.query(Comment).options(joinedload(Comment.user)).filter(Comment.notice_id == notice_id)
    total = query.count()
    items = (
        query.order_by(desc(Comment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return CommentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[CommentResponse.model_validate(c) for c in items],
    )


@router.post("", response_model=CommentResponse, summary="发布评论")
def create_comment(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登录用户发评论。"""
    notice = db.query(Notice).filter(Notice.id == comment_in.notice_id, Notice.status == 1).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")

    comment = Comment(
        notice_id=comment_in.notice_id,
        user_id=current_user.id,
        content=comment_in.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    comment.user  # 加载 user 关系
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=204, summary="删除评论")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """评论作者本人或管理员可删除。"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该评论")

    db.delete(comment)
    db.commit()