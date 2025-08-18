#!/usr/bin/env python3
#
# 功能: Flask应用的主入口点
#
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import create_app


def setup_logging():
    """设置日志配置"""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            (
                logging.FileHandler("logs/app.log")
                if os.path.exists("logs")
                else logging.NullHandler()
            ),
        ],
    )


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    # 获取配置
    config_name = os.environ.get("FLASK_ENV", "development")
    host = os.environ.get("FLASK_HOST", "0.0.0.0")

    # 安全地获取端口配置
    try:
        port = int(os.environ.get("FLASK_PORT", "5000"))
    except (ValueError, TypeError):
        logger.warning("FLASK_PORT 环境变量无效，使用默认端口 5000")
        port = 5000

    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    logger.info(f"启动VO-Benchmark API服务")
    logger.info(f"环境: {config_name}")
    logger.info(f"地址: {host}:{port}")
    logger.info(f"调试模式: {debug}")

    try:
        # 创建Flask应用
        app = create_app(config_name)

        # 启动应用（禁用自动重载，避免多进程端口竞争与超时）
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
