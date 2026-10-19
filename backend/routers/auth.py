# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from utils.auth import hash_password, verify_password, create_access_token, get_current_user, check_login_rate_limit
from utils.operation_log import log_operation

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=Token, summary="用户注册")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册",
        )
    db_user = User(
        username=user_in.username,
        password=hash_password(user_in.password),
        nickname=user_in.nickname or user_in.username,
        avatar=user_in.avatar,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_access_token({"user_id": db_user.id, "username": db_user.username, "role": db_user.role})
    return Token(access_token=token, user=UserResponse.model_validate(db_user))


@router.post("/login", response_model=Token, summary="用户登录")
def login(user_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    # 登录频率限制（基于客户端 IP）
    client_ip = _get_client_ip(request)
    check_login_rate_limit(client_ip)

    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"user_id": user.id, "username": user.username, "role": user.role})

    # 记录登录日志
    log_operation(
        db, user_id=user.id, username=user.username,
        action="login", detail=f"用户登录",
        ip=client_ip,
    )

    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login-oauth", response_model=Token, summary="OAuth2表单登录（兼容Swagger）")
def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    # 登录频率限制
    client_ip = _get_client_ip(request) if request else "unknown"
    check_login_rate_limit(client_ip)

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"user_id": user.id, "username": user.username, "role": user.role})

    log_operation(
        db, user_id=user.id, username=user.username,
        action="login", detail=f"用户登录(Swagger)",
        ip=client_ip,
    )

    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP，优先读取反向代理转发的 X-Forwarded-For"""
    if not request:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
