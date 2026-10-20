@echo off
chcp 65001 >nul
title Daisy Hair Salon - AI 预约助手
cd /d "%~dp0"

REM ============================================
REM   Daisy Hair Salon - AI Booking Assistant
REM   一键启动：双击本文件即可
REM ============================================

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [错误] 未找到虚拟环境 .venv
    echo 请先运行 setup.bat 安装依赖后再启动。
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   💇 Daisy Hair Salon - AI 预约助手
echo ============================================
echo.
echo   [1/2] 正在启动服务...
echo   服务地址: http://localhost:8000
echo   浏览器将自动打开...
echo.
echo   [2/2] 启动完成后，关闭此窗口即停止服务
echo.

REM 3 秒后自动打开浏览器（等服务起来）
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000"

REM 干净环境启动（避免外部 PYTHONPATH 污染）
set "PYTHONPATH="
set "PYTHONHOME="
set "VIRTUAL_ENV="
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000

echo.
echo 服务已停止。
pause
