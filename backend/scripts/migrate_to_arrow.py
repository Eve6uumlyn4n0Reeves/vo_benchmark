#!/usr/bin/env python3
"""
数据迁移脚本：将现有JSON数据转换为Arrow格式
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
import gzip

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.experiment import ExperimentStorage
from src.storage.arrow_writer import ArrowWriter, ARROW_AVAILABLE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self, storage_root: str, dry_run: bool = False):
        self.storage_root = Path(storage_root)
        self.dry_run = dry_run
        self.storage = ExperimentStorage(storage_root)
        
        if not ARROW_AVAILABLE:
            raise RuntimeError("PyArrow is required for migration")
        
        self.arrow_writer = ArrowWriter()
        
        # 统计信息
        self.stats = {
            'experiments_found': 0,
            'trajectories_migrated': 0,
            'pr_curves_migrated': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def discover_experiments(self) -> List[str]:
        """发现所有实验"""
        experiments_dir = self.storage_root / "experiments"
        if not experiments_dir.exists():
            logger.warning(f"实验目录不存在: {experiments_dir}")
            return []
        
        experiments = []
        for exp_dir in experiments_dir.iterdir():
            if exp_dir.is_dir():
                experiments.append(exp_dir.name)
        
        logger.info(f"发现 {len(experiments)} 个实验")
        self.stats['experiments_found'] = len(experiments)
        return experiments
    
    def discover_algorithms(self, experiment_id: str) -> List[str]:
        """发现实验中的所有算法"""
        algorithms = set()
        
        # 从轨迹目录发现
        traj_dir = self.storage_root / f"experiments/{experiment_id}/trajectories"
        if traj_dir.exists():
            for file in traj_dir.glob("*.json.gz"):
                algorithms.add(file.stem)
        
        # 从PR曲线目录发现
        pr_dir = self.storage_root / f"experiments/{experiment_id}/pr_curves"
        if pr_dir.exists():
            for file in pr_dir.glob("*.json.gz"):
                algorithms.add(file.stem)
        
        return list(algorithms)
    
    def migrate_trajectory(self, experiment_id: str, algorithm_key: str) -> bool:
        """迁移单个轨迹数据"""
        try:
            # 检查是否已经有Arrow文件
            arrow_ui_path = self.storage_root / f"experiments/{experiment_id}/trajectories/{algorithm_key}.ui.arrow"
            arrow_full_path = self.storage_root / f"experiments/{experiment_id}/trajectories/{algorithm_key}.arrow"
            
            if arrow_ui_path.exists() and arrow_full_path.exists():
                logger.debug(f"轨迹Arrow文件已存在，跳过: {experiment_id}/{algorithm_key}")
                self.stats['skipped'] += 1
                return True
            
            # 加载JSON数据
            trajectory_data = self.storage.get_trajectory(experiment_id, algorithm_key)
            if not trajectory_data:
                logger.debug(f"轨迹数据不存在: {experiment_id}/{algorithm_key}")
                return False
            
            # 提取轨迹数据
            estimated = trajectory_data.get("estimated_trajectory", [])
            groundtruth = trajectory_data.get("groundtruth_trajectory", [])
            reference = trajectory_data.get("reference_trajectory", [])
            metadata = trajectory_data.get("metadata", {})
            
            if not estimated:
                logger.warning(f"轨迹数据为空: {experiment_id}/{algorithm_key}")
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] 将迁移轨迹: {experiment_id}/{algorithm_key} ({len(estimated)} 点)")
                return True
            
            # 保存Full版本
            self.arrow_writer.write_trajectory(
                arrow_full_path,
                estimated,
                groundtruth,
                reference,
                {**metadata, "version": "full", "migrated": True}
            )
            
            # 创建UI版本（下采样）
            ui_estimated = self.arrow_writer.downsample_trajectory(estimated, max_points=1500)
            ui_groundtruth = self.arrow_writer.downsample_trajectory(groundtruth, max_points=1500) if groundtruth else None
            ui_reference = self.arrow_writer.downsample_trajectory(reference, max_points=1500) if reference else None
            
            self.arrow_writer.write_trajectory(
                arrow_ui_path,
                ui_estimated,
                ui_groundtruth,
                ui_reference,
                {**metadata, "version": "ui", "downsampled": len(estimated) > 1500, "original_points": len(estimated), "migrated": True}
            )
            
            logger.info(f"轨迹迁移完成: {experiment_id}/{algorithm_key} (Full: {len(estimated)} -> UI: {len(ui_estimated)})")
            self.stats['trajectories_migrated'] += 1
            return True
            
        except Exception as e:
            logger.error(f"轨迹迁移失败: {experiment_id}/{algorithm_key} - {e}")
            self.stats['errors'] += 1
            return False
    
    def migrate_pr_curve(self, experiment_id: str, algorithm_key: str) -> bool:
        """迁移单个PR曲线数据"""
        try:
            # 检查是否已经有Arrow文件
            arrow_ui_path = self.storage_root / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.ui.arrow"
            arrow_full_path = self.storage_root / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.arrow"
            
            if arrow_ui_path.exists() and arrow_full_path.exists():
                logger.debug(f"PR曲线Arrow文件已存在，跳过: {experiment_id}/{algorithm_key}")
                self.stats['skipped'] += 1
                return True
            
            # 加载JSON数据
            pr_data = self.storage.get_pr_curve(experiment_id, algorithm_key)
            if not pr_data:
                logger.debug(f"PR曲线数据不存在: {experiment_id}/{algorithm_key}")
                return False
            
            # 提取PR数据
            precisions = pr_data.get("precisions", [])
            recalls = pr_data.get("recalls", [])
            thresholds = pr_data.get("thresholds", [])
            f1_scores = pr_data.get("f1_scores", [])
            
            # 原始数据（如果存在）
            raw_precisions = pr_data.get("raw_precisions")
            raw_recalls = pr_data.get("raw_recalls")
            raw_thresholds = pr_data.get("raw_thresholds")
            raw_f1_scores = pr_data.get("raw_f1_scores")
            
            if not precisions or not recalls:
                logger.warning(f"PR曲线数据为空: {experiment_id}/{algorithm_key}")
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] 将迁移PR曲线: {experiment_id}/{algorithm_key} ({len(precisions)} 点)")
                return True
            
            # 元数据
            metadata = {
                "algorithm": pr_data.get("algorithm", algorithm_key),
                "auc_score": str(pr_data.get("auc_score", 0.0)),
                "optimal_threshold": str(pr_data.get("optimal_threshold", 0.0)),
                "optimal_precision": str(pr_data.get("optimal_precision", 0.0)),
                "optimal_recall": str(pr_data.get("optimal_recall", 0.0)),
                "max_f1_score": str(pr_data.get("max_f1_score", 0.0)),
                "migrated": "true"
            }
            
            # 保存Full版本
            self.arrow_writer.write_pr_curve(
                arrow_full_path,
                precisions, recalls, thresholds, f1_scores,
                raw_precisions, raw_recalls, raw_thresholds, raw_f1_scores,
                {**metadata, "version": "full"}
            )
            
            # 创建UI版本（下采样）
            ui_precisions, ui_recalls, ui_thresholds, ui_f1_scores = self.arrow_writer.downsample_pr_curve(
                precisions, recalls, thresholds, f1_scores, max_points=500
            )
            
            self.arrow_writer.write_pr_curve(
                arrow_ui_path,
                ui_precisions, ui_recalls, ui_thresholds, ui_f1_scores,
                metadata={**metadata, "version": "ui", "downsampled": len(precisions) > 500, "original_points": len(precisions)}
            )
            
            logger.info(f"PR曲线迁移完成: {experiment_id}/{algorithm_key} (Full: {len(precisions)} -> UI: {len(ui_precisions)})")
            self.stats['pr_curves_migrated'] += 1
            return True
            
        except Exception as e:
            logger.error(f"PR曲线迁移失败: {experiment_id}/{algorithm_key} - {e}")
            self.stats['errors'] += 1
            return False
    
    def migrate_experiment(self, experiment_id: str) -> None:
        """迁移单个实验的所有数据"""
        logger.info(f"开始迁移实验: {experiment_id}")
        
        algorithms = self.discover_algorithms(experiment_id)
        logger.info(f"实验 {experiment_id} 中发现 {len(algorithms)} 个算法")
        
        for algorithm_key in algorithms:
            logger.debug(f"迁移算法: {experiment_id}/{algorithm_key}")
            
            # 迁移轨迹数据
            self.migrate_trajectory(experiment_id, algorithm_key)
            
            # 迁移PR曲线数据
            self.migrate_pr_curve(experiment_id, algorithm_key)
            
            # 生成清单
            if not self.dry_run:
                try:
                    self.storage._manifest_manager.update_manifest_after_save(experiment_id, algorithm_key)
                    logger.debug(f"清单已更新: {experiment_id}/{algorithm_key}")
                except Exception as e:
                    logger.warning(f"清单更新失败: {experiment_id}/{algorithm_key} - {e}")
    
    def migrate_all(self, experiment_filter: str = None) -> None:
        """迁移所有数据"""
        experiments = self.discover_experiments()
        
        if experiment_filter:
            experiments = [exp for exp in experiments if experiment_filter in exp]
            logger.info(f"过滤后剩余 {len(experiments)} 个实验")
        
        for experiment_id in experiments:
            try:
                self.migrate_experiment(experiment_id)
            except Exception as e:
                logger.error(f"实验迁移失败: {experiment_id} - {e}")
                self.stats['errors'] += 1
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n" + "="*50)
        print("迁移统计信息")
        print("="*50)
        print(f"发现实验数量: {self.stats['experiments_found']}")
        print(f"轨迹迁移成功: {self.stats['trajectories_migrated']}")
        print(f"PR曲线迁移成功: {self.stats['pr_curves_migrated']}")
        print(f"跳过数量: {self.stats['skipped']}")
        print(f"错误数量: {self.stats['errors']}")
        print("="*50)


def main():
    parser = argparse.ArgumentParser(description="将现有JSON数据迁移到Arrow格式")
    parser.add_argument("--storage-root", required=True, help="存储根目录路径")
    parser.add_argument("--experiment", help="只迁移指定实验（支持部分匹配）")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要迁移的内容，不实际执行")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not ARROW_AVAILABLE:
        print("错误: PyArrow 未安装，无法执行迁移")
        sys.exit(1)
    
    storage_root = Path(args.storage_root)
    if not storage_root.exists():
        print(f"错误: 存储根目录不存在: {storage_root}")
        sys.exit(1)
    
    print(f"开始数据迁移...")
    print(f"存储根目录: {storage_root}")
    print(f"实验过滤: {args.experiment or '无'}")
    print(f"模式: {'预览模式' if args.dry_run else '实际迁移'}")
    print()
    
    migrator = DataMigrator(str(storage_root), dry_run=args.dry_run)
    
    try:
        migrator.migrate_all(args.experiment)
        migrator.print_stats()
        
        if args.dry_run:
            print("\n这是预览模式，没有实际修改任何文件。")
            print("要执行实际迁移，请移除 --dry-run 参数。")
        else:
            print("\n迁移完成！")
            
    except KeyboardInterrupt:
        print("\n迁移被用户中断")
        migrator.print_stats()
        sys.exit(1)
    except Exception as e:
        print(f"\n迁移失败: {e}")
        migrator.print_stats()
        sys.exit(1)


if __name__ == "__main__":
    main()
