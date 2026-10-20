@echo off
chcp 65001 >nul
title Daisy Hair Salon - 一键安装
cd /d "%~dp0"

echo.
echo ============================================
echo   💇 Daisy Hair Salon - AI 预约助手
echo   一键安装依赖
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并勾选 "Add to PATH"
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 创建虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [1/2] 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
) else (
    echo [1/2] 虚拟环境已存在，跳过创建
)

echo [2/2] 正在安装依赖（可能需要几分钟）...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
.venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo ✅ 安装完成！
echo.
echo 下一步：双击 start.bat 启动服务；编辑 .env 可切换模型。
echo.
pause
