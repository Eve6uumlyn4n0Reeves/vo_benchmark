@echo off
chcp 65001 >nul
title VO-Benchmark 启动脚本

echo.
echo ========================================
echo   VO-Benchmark 项目启动脚本 (Windows)
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请安装Node.js 16+并添加到系统PATH
    pause
    exit /b 1
)

REM 检查npm是否安装
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm未安装或未添加到PATH
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 运行Python启动脚本
echo 🚀 启动VO-Benchmark项目...
python setup.py

pause
