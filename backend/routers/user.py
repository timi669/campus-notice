# -*- coding: utf-8 -*-
import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from models.user import User
from schemas.user import UserUpdate, UserResponse, UserListItem, PasswordChange, RoleUpdate
from utils.auth import get_current_user, require_admin, hash_password, verify_password
from utils.operation_log import log_operation

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse, summary="修改当前用户信息（昵称/头像）")
def update_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = user_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.put("/me/password", response_model=dict, summary="修改当前用户密码（需校验旧密码）")
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="旧密码不正确")
    if body.old_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    current_user.password = hash_password(body.new_password)
    db.commit()
    return {"code": 0, "message": "密码修改成功"}


@router.delete("/me", status_code=200, summary="注销当前用户账号")
def deactivate_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户注销自己的账号。管理员不允许自注销（防止无人管理）。"""
    if current_user.role == "admin":
        raise HTTPException(status_code=400, detail="管理员账号不允许注销")
    username = current_user.username
    user_id = current_user.id
    db.delete(current_user)
    db.commit()
    return {"code": 0, "message": "账号已注销", "username": username, "user_id": user_id}


@router.get("", response_model=dict, summary="用户列表（管理员）")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX),
    keyword: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        from sqlalchemy import or_
        q = q.filter(or_(User.username.like(like), User.nickname.like(like)))
    if role:
        q = q.filter(User.role == role)
    total = q.count()
    users = q.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [UserListItem.model_validate(u) for u in users],
    }


@router.get("/export.csv", summary="导出用户列表 CSV（管理员）")
def export_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """导出所有用户为 CSV 文件。

    注意：本路由必须定义在 `/{user_id}` 之前，否则 "export.csv" 会被当作 user_id 解析而报 422。
    """
    users = db.query(User).order_by(desc(User.created_at)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "用户名", "昵称", "角色", "创建时间"])
    for u in users:
        writer.writerow([
            u.id, u.username, u.nickname or "", u.role,
            u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    output.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=users.csv",
        "Content-Type": "text/csv; charset=utf-8",
    }

    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="export", target_type="user", detail="导出用户列表CSV",
        ip=_get_client_ip(request),
    )

    return StreamingResponse(iter([output.getvalue()]), headers=headers)


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情（管理员）")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204, summary="删除用户（管理员）")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    username = user.username
    db.delete(user)
    db.commit()

    # 记录操作日志
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="delete", target_type="user", target_id=user_id,
        detail=f"删除用户: {username}",
        ip=_get_client_ip(request),
    )


@router.put("/{user_id}/role", response_model=UserResponse, summary="修改用户角色（管理员）")
def update_role(
    user_id: int,
    body: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    role = body.role
    if role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="角色不合法")
    if user_id == current_user.id and role != "admin":
        raise HTTPException(status_code=400, detail="不能降级自己的管理员角色")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    old_role = user.role
    user.role = role
    db.commit()
    db.refresh(user)

    # 记录操作日志
    log_operation(
        db, user_id=current_user.id, username=current_user.username,
        action="update_role", target_type="user", target_id=user_id,
        detail=f"修改角色 {user.username}: {old_role} -> {role}",
        ip=_get_client_ip(request),
    )

    return UserResponse.model_validate(user)


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    if not request:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
