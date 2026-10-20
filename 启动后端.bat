@echo off
chcp 65001 >nul
title 校园公告后端服务
cd /d D:\campus-notice\backend
echo ============================================
echo   校园公告资讯小程序 - 后端服务
echo ============================================
echo.
echo 正在启动后端服务...
echo 启动后访问: http://127.0.0.1:8000/docs
echo 按 Ctrl+C 停止服务
echo.
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
pause