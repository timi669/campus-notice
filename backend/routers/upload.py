# -*- coding: utf-8 -*-
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from config import settings
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 允许的图片类型
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", summary="上传图片（需登录）")
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    current_user: User = Depends(get_current_user),
):
    # 校验文件类型
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp/bmp 格式图片")

    # 校验扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="文件扩展名不支持")

    # 读取并校验大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    # 生成唯一文件名：日期 + uuid
    date_str = datetime.now().strftime("%Y%m%d")
    unique_name = f"{date_str}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # 返回可访问的 URL（通过 /uploads 静态路径访问）
    file_url = f"/uploads/{unique_name}"
    return {
        "code": 0,
        "message": "上传成功",
        "data": {
            "url": file_url,
            "filename": unique_name,
            "size": len(content),
        },
    }
