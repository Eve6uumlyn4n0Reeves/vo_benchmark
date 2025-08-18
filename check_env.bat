@echo off
chcp 65001 >nul
title VO-Benchmark 环境检查

echo.
echo ========================================
echo   VO-Benchmark 环境检查工具
echo ========================================
echo.

echo 🔍 检查基础环境...
echo.

REM 检查Python
echo [1/6] 检查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
) else (
    echo ❌ Python 未安装
    echo 💡 请访问 https://www.python.org/downloads/ 下载安装
)

REM 检查Node.js
echo [2/6] 检查 Node.js...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do echo ✅ Node.js %%i
) else (
    echo ❌ Node.js 未安装
    echo 💡 请访问 https://nodejs.org/ 下载安装
)

REM 检查npm
echo [3/6] 检查 npm...
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('npm --version') do echo ✅ npm %%i
) else (
    echo ❌ npm 未安装
)

REM 检查pip镜像配置
echo [4/6] 检查 pip 镜像配置...
if exist "%APPDATA%\pip\pip.ini" (
    echo ✅ pip 镜像已配置
) else (
    echo ⚠️ pip 镜像未配置
    echo 💡 建议配置国内镜像源以加速下载
)

REM 检查npm镜像配置
echo [5/6] 检查 npm 镜像配置...
for /f "tokens=*" %%i in ('npm config get registry') do (
    if "%%i"=="https://registry.npmmirror.com/" (
        echo ✅ npm 镜像已配置 (淘宝镜像)
    ) else if "%%i"=="https://registry.npmjs.org/" (
        echo ⚠️ npm 使用官方源 (可能较慢)
        echo 💡 建议配置淘宝镜像: npm config set registry https://registry.npmmirror.com
    ) else (
        echo ✅ npm 镜像: %%i
    )
)

REM 检查项目目录
echo [6/6] 检查项目结构...
if exist "backend" (
    echo ✅ backend 目录存在
) else (
    echo ❌ backend 目录不存在
)

if exist "frontend" (
    echo ✅ frontend 目录存在
) else (
    echo ❌ frontend 目录不存在
)

if exist "backend\venv" (
    echo ✅ Python 虚拟环境已创建
) else (
    echo ⚠️ Python 虚拟环境未创建
)

if exist "frontend\node_modules" (
    echo ✅ 前端依赖已安装
) else (
    echo ⚠️ 前端依赖未安装
)

echo.
echo ========================================
echo   检查完成
echo ========================================
echo.

REM 给出建议
if exist "backend\venv" if exist "frontend\node_modules" (
    echo 🎉 环境配置完成！可以直接启动项目
    echo.
    echo 启动命令：
    echo   后端: cd backend ^&^& venv\Scripts\activate ^&^& python start_server.py
    echo   前端: cd frontend ^&^& npm run dev
    echo.
    echo 或者查看 QUICK_START.md 获取详细启动指令
) else (
    echo 📋 需要完成环境配置
    echo.
    echo 请按照 SETUP_GUIDE.md 完成配置：
    if not exist "backend\venv" echo   - 配置后端环境
    if not exist "frontend\node_modules" echo   - 配置前端环境
)

echo.
pause
