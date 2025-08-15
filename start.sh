#!/bin/bash

# VO-Benchmark 项目启动脚本 (Linux/macOS)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印彩色消息
print_colored() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo
    print_colored $PURPLE "========================================"
    print_colored $PURPLE "  $1"
    print_colored $PURPLE "========================================"
    echo
}

print_header "VO-Benchmark 项目启动脚本 (Linux/macOS)"

# 检查Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_colored $RED "❌ Python未安装"
        print_colored $YELLOW "请安装Python 3.8+"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_colored $RED "❌ Python版本过低: $PYTHON_VERSION"
    print_colored $YELLOW "需要Python 3.8+"
    exit 1
fi

print_colored $GREEN "✅ Python $PYTHON_VERSION"

# 检查Node.js
if ! command -v node &> /dev/null; then
    print_colored $RED "❌ Node.js未安装"
    print_colored $YELLOW "请安装Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)

if [ "$NODE_MAJOR" -lt 16 ]; then
    print_colored $RED "❌ Node.js版本过低: $NODE_VERSION"
    print_colored $YELLOW "需要Node.js 16+"
    exit 1
fi

print_colored $GREEN "✅ Node.js $NODE_VERSION"

# 检查npm
if ! command -v npm &> /dev/null; then
    print_colored $RED "❌ npm未安装"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_colored $GREEN "✅ npm $NPM_VERSION"

echo
print_colored $BLUE "🚀 启动VO-Benchmark项目..."

# 运行Python启动脚本
$PYTHON_CMD setup.py
