#
# 功能: 定义后台任务工作线程。
#
import threading
import time
import logging
from queue import Queue, Empty
from typing import Dict, Any, Optional, Callable
from src.models.types import TaskStatus
from src.models.experiment import AlgorithmRun
from src.pipeline.manager import ExperimentManager

logger = logging.getLogger(__name__)


class TaskWorker:
    """后台任务工作线程"""

    def __init__(self, task_queue: Queue, result_queue: Queue, worker_id: int = 0):
        """
        初始化任务工作线程

        Args:
            task_queue: 任务队列
            result_queue: 结果队列
            worker_id: 工作线程ID
        """
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.worker_id = worker_id
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        logger.info(f"初始化任务工作线程 {worker_id}")

    def start(self) -> None:
        """启动工作线程"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning(f"工作线程 {self.worker_id} 已经在运行")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self.run, name=f"TaskWorker-{self.worker_id}"
        )
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"启动工作线程 {self.worker_id}")

    def stop(self, timeout: float = 5.0) -> bool:
        """
        停止工作线程

        Args:
            timeout: 等待超时时间（秒）

        Returns:
            bool: 是否成功停止
        """
        if self._thread is None or not self._thread.is_alive():
            return True

        logger.info(f"停止工作线程 {self.worker_id}")
        self._stop_event.set()
        self._thread.join(timeout)

        if self._thread.is_alive():
            logger.warning(f"工作线程 {self.worker_id} 未能在超时时间内停止")
            return False

        logger.info(f"工作线程 {self.worker_id} 已停止")
        return True

    def run(self) -> None:
        """任务处理主循环"""
        logger.info(f"工作线程 {self.worker_id} 开始运行")

        while not self._stop_event.is_set():
            try:
                # 从队列获取任务（带超时）
                task = self.task_queue.get(timeout=1.0)

                if task is None:  # 毒丸信号，停止工作线程
                    logger.info(f"工作线程 {self.worker_id} 收到停止信号")
                    break

                # 处理任务
                result = self.process_task(task)

                # 将结果放入结果队列
                self.result_queue.put(
                    {
                        "task_id": task.get("task_id"),
                        "worker_id": self.worker_id,
                        "result": result,
                        "status": (
                            "completed" if result.get("success", False) else "failed"
                        ),
                        "timestamp": time.time(),
                    }
                )

                # 标记任务完成
                self.task_queue.task_done()

            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"工作线程 {self.worker_id} 处理任务时发生错误: {e}")
                # 将错误结果放入结果队列
                self.result_queue.put(
                    {
                        "task_id": task.get("task_id", "unknown"),
                        "worker_id": self.worker_id,
                        "result": {"success": False, "error": str(e)},
                        "status": "failed",
                        "timestamp": time.time(),
                    }
                )

                if "task" in locals():
                    self.task_queue.task_done()

        logger.info(f"工作线程 {self.worker_id} 运行结束")

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个任务

        Args:
            task: 任务字典，包含任务类型和参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        task_type = task.get("type")
        task_id = task.get("task_id", "unknown")

        logger.debug(
            f"工作线程 {self.worker_id} 开始处理任务 {task_id} (类型: {task_type})"
        )

        try:
            if task_type == "run_algorithm":
                return self._process_algorithm_task(task)
            elif task_type == "run_experiment":
                return self._process_experiment_task(task)
            else:
                logger.error(f"未知的任务类型: {task_type}")
                return {
                    "success": False,
                    "error": f"未知的任务类型: {task_type}",
                    "task_id": task_id,
                }

        except Exception as e:
            logger.error(f"处理任务 {task_id} 时发生错误: {e}")
            return {"success": False, "error": str(e), "task_id": task_id}

    def _process_algorithm_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理算法运行任务"""
        try:
            algorithm_run = AlgorithmRun(**task["algorithm_run"])
            experiment_manager = task["experiment_manager"]
            progress_callback = task.get("progress_callback")

            # 执行算法运行
            metrics = experiment_manager.run_algorithm(algorithm_run, progress_callback)

            return {
                "success": True,
                "metrics": metrics,
                "algorithm_key": algorithm_run.algorithm_key,
                "task_id": task["task_id"],
            }

        except Exception as e:
            logger.error(f"算法任务执行失败: {e}")
            return {"success": False, "error": str(e), "task_id": task["task_id"]}

    def _process_experiment_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理实验任务"""
        try:
            experiment_config = task["experiment_config"]
            experiment_id = task["experiment_id"]
            storage = task["storage"]
            progress_callback = task.get("progress_callback")

            # 创建实验管理器
            experiment_manager = ExperimentManager(experiment_config, storage)

            # 执行实验
            results = experiment_manager.run_experiment(
                experiment_id, progress_callback
            )

            return {
                "success": True,
                "results": results,
                "experiment_id": experiment_id,
                "task_id": task["task_id"],
            }

        except Exception as e:
            logger.error(f"实验任务执行失败: {e}")
            return {"success": False, "error": str(e), "task_id": task["task_id"]}

    def is_running(self) -> bool:
        """检查工作线程是否正在运行"""
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )
