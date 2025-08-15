"""API模块 - Web服务接口层

提供Flask应用、路由、服务、模式验证和异常处理的完整API框架。
"""

from .app import create_app

__all__ = [
    "create_app",
]
