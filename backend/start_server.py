#!/usr/bin/env python3
"""
VO-Benchmark Backend Server Startup Script

This script properly configures the Python path and starts the backend server
with all necessary environment variables and configurations.

Usage:
    python start_server.py
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path so we can import the 'src' package
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up environment variables
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_HOST', '0.0.0.0')
os.environ.setdefault('FLASK_PORT', '5000')
os.environ.setdefault('FLASK_DEBUG', 'true')

# Note: DATABASE_URL and REDIS_URL are optional placeholders for future use
# Current implementation uses file-based storage and in-memory task management
os.environ.setdefault('DATABASE_URL', 'sqlite:///vo_benchmark.db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')

# 安全配置
if not os.environ.get('SECRET_KEY'):
    import secrets
    secret_key = secrets.token_urlsafe(32)
    os.environ.setdefault('SECRET_KEY', secret_key)
    logging.getLogger(__name__).warning("使用临时生成的SECRET_KEY，生产环境请设置环境变量")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_directories():
    """创建必要的目录"""
    directories = [
        backend_dir / 'data',
        backend_dir / 'data' / 'experiments',
        backend_dir / 'data' / 'datasets',
        backend_dir / 'results',  # 统一后端默认结果目录
        backend_dir / 'logs'
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    logger.info("必要目录已创建")

def ensure_results_root_env():
    """不再隐式覆盖 RESULTS_ROOT。仅在缺失时输出提示，实际统一由 ConfigManager 管理。
    保持向后兼容：如果已设置则记录；未设置则提示最好在配置文件或环境变量中显式配置。
    """
    try:
        if os.environ.get('RESULTS_ROOT'):
            logger.info(f"RESULTS_ROOT 已设置为: {os.environ.get('RESULTS_ROOT')}")
        else:
            logger.info(
                "RESULTS_ROOT 未设置，将由配置管理器默认值决定（storage.results_root）。"
            )
    except Exception as e:
        logger.warning(f"检查 RESULTS_ROOT 失败（忽略）: {e}")

def main():
    """Main function to start the server"""
    try:
        logger.info("🚀 启动VO-Benchmark真实后端服务器...")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"当前工作目录: {os.getcwd()}")

        # 创建必要目录与结果根环境变量
        create_directories()
        ensure_results_root_env()

        # 直接导入，无需切换工作目录

        # Import and run the main application
        logger.info("正在导入应用模块...")
        from src.main import main as app_main

        logger.info("✅ 应用模块导入成功")
        logger.info("🌟 启动Flask服务器...")

        app_main()

    except ImportError as e:
        logger.error(f"❌ 导入错误: {e}")
        logger.error("请检查依赖是否已安装：pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
