#!/usr/bin/env python3
"""
VO-Benchmark 项目环境配置与启动脚本
支持自动检测环境、安装依赖、启动服务器
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from typing import Optional, List, Tuple

class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message: str, color: str = Colors.ENDC):
    """打印彩色消息"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message: str):
    """打印标题"""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f" {message}", Colors.HEADER + Colors.BOLD)
    print_colored(f"{'='*60}", Colors.HEADER)

def run_command(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=check
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, f"命令未找到: {' '.join(cmd)}"

def check_python_version() -> bool:
    """检查Python版本"""
    print_colored("🐍 检查Python版本...", Colors.OKBLUE)
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro}", Colors.OKGREEN)
        return True
    else:
        print_colored(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}", Colors.FAIL)
        print_colored("需要Python 3.8+", Colors.WARNING)
        return False

def check_node_version() -> bool:
    """检查Node.js版本"""
    print_colored("📦 检查Node.js版本...", Colors.OKBLUE)
    success, output = run_command(["node", "--version"], check=False)
    if success:
        version = output.replace('v', '')
        major_version = int(version.split('.')[0])
        if major_version >= 16:
            print_colored(f"✅ Node.js {version}", Colors.OKGREEN)
            return True
        else:
            print_colored(f"❌ Node.js版本过低: {version}", Colors.FAIL)
            print_colored("需要Node.js 16+", Colors.WARNING)
            return False
    else:
        print_colored("❌ Node.js未安装", Colors.FAIL)
        return False

def check_npm_version() -> bool:
    """检查npm版本"""
    print_colored("📦 检查npm版本...", Colors.OKBLUE)
    success, output = run_command(["npm", "--version"], check=False)
    if success:
        print_colored(f"✅ npm {output}", Colors.OKGREEN)
        return True
    else:
        print_colored("❌ npm未安装", Colors.FAIL)
        return False

def setup_backend() -> bool:
    """设置后端环境"""
    print_header("设置后端环境 (Flask)")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_colored("❌ backend目录不存在", Colors.FAIL)
        return False
    
    # 检查虚拟环境
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print_colored("🔧 创建Python虚拟环境...", Colors.OKBLUE)
        success, output = run_command([sys.executable, "-m", "venv", "venv"], cwd=backend_dir)
        if not success:
            print_colored(f"❌ 创建虚拟环境失败: {output}", Colors.FAIL)
            return False
        print_colored("✅ 虚拟环境创建成功", Colors.OKGREEN)
    
    # 激活虚拟环境的pip路径
    if platform.system() == "Windows":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
    
    # 检查requirements.txt
    requirements_file = backend_dir / "requirements.txt"
    if requirements_file.exists():
        print_colored("📦 安装Python依赖...", Colors.OKBLUE)
        success, output = run_command([str(pip_path), "install", "-r", "requirements.txt"], cwd=backend_dir)
        if not success:
            print_colored(f"❌ 安装依赖失败: {output}", Colors.FAIL)
            return False
        print_colored("✅ Python依赖安装成功", Colors.OKGREEN)
    
    return True

def setup_frontend() -> bool:
    """设置前端环境"""
    print_header("设置前端环境 (React + Vite)")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_colored("❌ frontend目录不存在", Colors.FAIL)
        return False
    
    # 检查package.json
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print_colored("❌ package.json不存在", Colors.FAIL)
        return False
    
    # 检查node_modules
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print_colored("📦 安装前端依赖...", Colors.OKBLUE)
        success, output = run_command(["npm", "install"], cwd=frontend_dir)
        if not success:
            print_colored(f"❌ 安装依赖失败: {output}", Colors.FAIL)
            return False
        print_colored("✅ 前端依赖安装成功", Colors.OKGREEN)
    else:
        print_colored("✅ 前端依赖已安装", Colors.OKGREEN)
    
    return True

def start_backend() -> subprocess.Popen:
    """启动后端服务器"""
    print_colored("🚀 启动后端服务器...", Colors.OKBLUE)
    
    backend_dir = Path("backend")
    
    # 确定Python路径
    if platform.system() == "Windows":
        python_path = backend_dir / "venv" / "Scripts" / "python.exe"
    else:
        python_path = backend_dir / "venv" / "bin" / "python"
    
    # 启动Flask服务器
    try:
        process = subprocess.Popen(
            [str(python_path), "start_server.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print_colored("✅ 后端服务器启动中... (端口: 5000)", Colors.OKGREEN)
        return process
    except Exception as e:
        print_colored(f"❌ 启动后端失败: {e}", Colors.FAIL)
        return None

def start_frontend() -> subprocess.Popen:
    """启动前端开发服务器"""
    print_colored("🚀 启动前端开发服务器...", Colors.OKBLUE)
    
    frontend_dir = Path("frontend")
    
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print_colored("✅ 前端开发服务器启动中... (端口: 3000)", Colors.OKGREEN)
        return process
    except Exception as e:
        print_colored(f"❌ 启动前端失败: {e}", Colors.FAIL)
        return None

def wait_for_servers():
    """等待服务器启动并显示状态"""
    print_header("服务器状态")
    
    # 等待几秒让服务器启动
    time.sleep(3)
    
    # 检查后端
    success, _ = run_command(["curl", "-s", "http://127.0.0.1:5000/api/v1/health"], check=False)
    if success:
        print_colored("✅ 后端服务器运行正常: http://127.0.0.1:5000", Colors.OKGREEN)
    else:
        print_colored("⏳ 后端服务器启动中...", Colors.WARNING)
    
    # 检查前端
    success, _ = run_command(["curl", "-s", "http://127.0.0.1:3000"], check=False)
    if success:
        print_colored("✅ 前端服务器运行正常: http://127.0.0.1:3000", Colors.OKGREEN)
    else:
        print_colored("⏳ 前端服务器启动中...", Colors.WARNING)
    
    print_colored("\n🌐 访问应用: http://127.0.0.1:3000", Colors.OKGREEN + Colors.BOLD)
    print_colored("📚 API文档: http://127.0.0.1:5000/api/v1/health", Colors.OKBLUE)

def main():
    """主函数"""
    print_header("VO-Benchmark 项目启动脚本")
    print_colored("Flask（后端）与 React + Vite（前端）", Colors.OKCYAN)
    
    # 检查系统要求
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    if not check_npm_version():
        sys.exit(1)
    
    # 设置环境
    if not setup_backend():
        print_colored("❌ 后端环境设置失败", Colors.FAIL)
        sys.exit(1)
    
    if not setup_frontend():
        print_colored("❌ 前端环境设置失败", Colors.FAIL)
        sys.exit(1)
    
    # 启动服务器
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    # 等待并显示状态
    wait_for_servers()
    
    try:
        print_colored("\n按 Ctrl+C 停止所有服务器", Colors.WARNING)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\n🛑 正在停止服务器...", Colors.WARNING)
        backend_process.terminate()
        frontend_process.terminate()
        print_colored("✅ 所有服务器已停止", Colors.OKGREEN)

if __name__ == "__main__":
    main()
