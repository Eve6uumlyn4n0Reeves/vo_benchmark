"""API路由模块 - REST端点定义

包含所有API端点的路由定义和处理逻辑。
"""

from .tasks import bp as tasks_bp
from .results import bp as results_bp
from .events import bp as events_bp
from .datasets import bp as datasets_bp

# Legacy blueprints removed - use documented versions instead
health_bp = None
experiments_bp = None

__all__ = [
    "tasks_bp",
    "results_bp",
    "events_bp",
    "datasets_bp",
    "health_bp",
    "experiments_bp",
]
