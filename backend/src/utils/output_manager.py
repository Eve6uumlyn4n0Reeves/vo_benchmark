#!/usr/bin/env python3
"""
输出目录管理器
负责创建和管理实验输出目录的标准化结构
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OutputDirectoryConfig:
    """输出目录配置"""

    root_dir: str
    experiment_id: str
    experiment_name: str
    dataset_name: str
    timestamp: str


class OutputDirectoryManager:
    """输出目录管理器"""

    def __init__(self, root_output_dir: str | None = None):
        """
        初始化输出目录管理器

        Args:
            root_output_dir: 输出根目录路径（优先使用提供的路径；否则从配置 RESULTS_ROOT/experiments 获取；仍无则回退 ./data/results/experiments）
        """
        # 尝试从 Flask 配置获取
        if root_output_dir is None:
            try:
                from flask import current_app

                if current_app and hasattr(current_app, "config"):
                    results_root = current_app.config.get("RESULTS_ROOT")
                    if results_root:
                        root_output_dir = str(Path(results_root) / "experiments")
            except Exception:
                root_output_dir = None
        if root_output_dir is None:
            root_output_dir = "./data/results/experiments"
        self.root_output_dir = Path(root_output_dir).resolve()
        self.ensure_root_directory()

    def ensure_root_directory(self):
        """确保根目录存在"""
        self.root_output_dir.mkdir(parents=True, exist_ok=True)

    def generate_experiment_id(self, experiment_name: str) -> str:
        """
        生成实验ID

        Args:
            experiment_name: 实验名称

        Returns:
            格式化的实验ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理实验名称，移除特殊字符
        clean_name = "".join(
            c for c in experiment_name if c.isalnum() or c in "_-"
        ).lower()
        return f"{clean_name}_{timestamp}"

    def create_experiment_directory(
        self,
        experiment_name: str,
        dataset_name: str,
        experiment_id: Optional[str] = None,
    ) -> OutputDirectoryConfig:
        """
        创建实验目录结构

        Args:
            experiment_name: 实验名称
            dataset_name: 数据集名称
            experiment_id: 可选的实验ID，如果不提供则自动生成

        Returns:
            输出目录配置对象
        """
        if experiment_id is None:
            experiment_id = self.generate_experiment_id(experiment_name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 创建实验目录
        experiment_dir = self.root_output_dir / experiment_id
        experiment_dir.mkdir(parents=True, exist_ok=True)

        # 创建标准子目录结构
        subdirs = [
            "results",  # 实验结果文件
            "results/trajectories",  # 轨迹数据
            "results/metrics",  # 评估指标
            "results/visualizations",  # 可视化图表
            "logs",  # 日志文件
            "cache",  # 缓存文件
            "config",  # 配置文件
            "raw_data",  # 原始数据
            "raw_data/features",  # 特征数据
            "raw_data/matches",  # 匹配数据
            "reports",  # 报告文件
        ]

        for subdir in subdirs:
            (experiment_dir / subdir).mkdir(parents=True, exist_ok=True)

        # 创建配置对象
        config = OutputDirectoryConfig(
            root_dir=str(experiment_dir),
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            dataset_name=dataset_name,
            timestamp=timestamp,
        )

        # 保存目录配置信息
        self._save_directory_info(experiment_dir, config)

        return config

    def _save_directory_info(self, experiment_dir: Path, config: OutputDirectoryConfig):
        """保存目录配置信息到文件"""
        info_file = experiment_dir / "config" / "directory_info.json"

        directory_info = {
            "experiment_id": config.experiment_id,
            "experiment_name": config.experiment_name,
            "dataset_name": config.dataset_name,
            "created_at": config.timestamp,
            "directory_structure": {
                "results": "实验结果文件",
                "results/trajectories": "轨迹数据文件",
                "results/metrics": "评估指标文件",
                "results/visualizations": "可视化图表文件",
                "logs": "运行日志文件",
                "cache": "缓存文件",
                "config": "配置文件",
                "raw_data": "原始数据文件",
                "raw_data/features": "特征提取数据",
                "raw_data/matches": "特征匹配数据",
                "reports": "实验报告文件",
            },
        }

        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(directory_info, f, indent=2, ensure_ascii=False)

    def get_experiment_path(self, experiment_id: str) -> Optional[Path]:
        """
        获取实验目录路径

        Args:
            experiment_id: 实验ID

        Returns:
            实验目录路径，如果不存在则返回None
        """
        experiment_dir = self.root_output_dir / experiment_id
        return experiment_dir if experiment_dir.exists() else None

    def list_experiments(self) -> list[Dict[str, Any]]:
        """
        列出所有实验

        Returns:
            实验信息列表
        """
        experiments = []

        for item in self.root_output_dir.iterdir():
            if item.is_dir():
                info_file = item / "config" / "directory_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            info = json.load(f)
                            experiments.append(
                                {
                                    "experiment_id": info.get("experiment_id"),
                                    "experiment_name": info.get("experiment_name"),
                                    "dataset_name": info.get("dataset_name"),
                                    "created_at": info.get("created_at"),
                                    "path": str(item),
                                }
                            )
                    except Exception as e:
                        # 如果读取配置文件失败，跳过该目录
                        continue

        return sorted(experiments, key=lambda x: x["created_at"], reverse=True)

    def cleanup_old_experiments(self, keep_days: int = 30):
        """
        清理旧的实验目录

        Args:
            keep_days: 保留天数
        """
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)

        for item in self.root_output_dir.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff_date:
                # 这里可以添加更安全的删除逻辑
                pass

    def get_directory_size(self, experiment_id: str) -> int:
        """
        获取实验目录大小

        Args:
            experiment_id: 实验ID

        Returns:
            目录大小（字节）
        """
        experiment_dir = self.get_experiment_path(experiment_id)
        if not experiment_dir:
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(experiment_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass

        return total_size


# 全局实例
output_manager = OutputDirectoryManager()
