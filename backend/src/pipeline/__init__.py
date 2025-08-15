"""管道模块 - 任务处理流水线

提供帧处理器、实验管理器和工作线程的任务处理管道。
"""

from src.pipeline.processor import FrameProcessor
from src.pipeline.manager import ExperimentManager
from src.pipeline.worker import TaskWorker

__all__ = ["FrameProcessor", "ExperimentManager", "TaskWorker"]
