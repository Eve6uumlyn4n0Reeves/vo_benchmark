#!/usr/bin/env python3
"""
清理脚本：移除已迁移的旧JSON文件和未使用的代码
"""

import argparse
import logging
import sys
import shutil
from pathlib import Path
from typing import List, Set
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LegacyCleaner:
    """遗留文件清理器"""
    
    def __init__(self, storage_root: str, dry_run: bool = False):
        self.storage_root = Path(storage_root)
        self.dry_run = dry_run
        
        # 统计信息
        self.stats = {
            'json_files_found': 0,
            'json_files_removed': 0,
            'arrow_files_found': 0,
            'bytes_saved': 0,
            'errors': 0
        }
    
    def find_legacy_files(self) -> List[Path]:
        """查找可以清理的遗留文件"""
        legacy_files = []
        
        experiments_dir = self.storage_root / "experiments"
        if not experiments_dir.exists():
            logger.warning(f"实验目录不存在: {experiments_dir}")
            return legacy_files
        
        for exp_dir in experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            # 查找轨迹JSON文件
            traj_dir = exp_dir / "trajectories"
            if traj_dir.exists():
                for json_file in traj_dir.glob("*.json.gz"):
                    # 检查是否有对应的Arrow文件
                    ui_arrow = traj_dir / f"{json_file.stem}.ui.arrow"
                    full_arrow = traj_dir / f"{json_file.stem}.arrow"
                    
                    if ui_arrow.exists() and full_arrow.exists():
                        legacy_files.append(json_file)
                        self.stats['json_files_found'] += 1
            
            # 查找PR曲线JSON文件
            pr_dir = exp_dir / "pr_curves"
            if pr_dir.exists():
                for json_file in pr_dir.glob("*.json.gz"):
                    # 检查是否有对应的Arrow文件
                    ui_arrow = pr_dir / f"{json_file.stem}.ui.arrow"
                    full_arrow = pr_dir / f"{json_file.stem}.arrow"
                    
                    if ui_arrow.exists() and full_arrow.exists():
                        legacy_files.append(json_file)
                        self.stats['json_files_found'] += 1
        
        # 统计Arrow文件
        for exp_dir in experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            for arrow_file in exp_dir.rglob("*.arrow"):
                self.stats['arrow_files_found'] += 1
        
        logger.info(f"发现 {len(legacy_files)} 个可清理的JSON文件")
        logger.info(f"发现 {self.stats['arrow_files_found']} 个Arrow文件")
        
        return legacy_files
    
    def verify_arrow_integrity(self, json_path: Path) -> bool:
        """验证对应的Arrow文件完整性"""
        try:
            from src.storage.arrow_writer import ArrowReader, ARROW_AVAILABLE
            
            if not ARROW_AVAILABLE:
                logger.warning("PyArrow不可用，跳过完整性检查")
                return True
            
            reader = ArrowReader()
            
            # 检查UI版本
            ui_arrow = json_path.parent / f"{json_path.stem}.ui.arrow"
            if ui_arrow.exists():
                ui_data = reader.read_trajectory(ui_arrow) if "trajectories" in str(json_path) else reader.read_pr_curve(ui_arrow)
                if not ui_data:
                    logger.error(f"Arrow UI文件损坏: {ui_arrow}")
                    return False
            
            # 检查Full版本
            full_arrow = json_path.parent / f"{json_path.stem}.arrow"
            if full_arrow.exists():
                full_data = reader.read_trajectory(full_arrow) if "trajectories" in str(json_path) else reader.read_pr_curve(full_arrow)
                if not full_data:
                    logger.error(f"Arrow Full文件损坏: {full_arrow}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Arrow完整性检查失败: {json_path} - {e}")
            return False
    
    def remove_legacy_file(self, file_path: Path) -> bool:
        """移除单个遗留文件"""
        try:
            if not self.verify_arrow_integrity(file_path):
                logger.warning(f"Arrow文件完整性检查失败，跳过删除: {file_path}")
                return False
            
            file_size = file_path.stat().st_size
            
            if self.dry_run:
                logger.info(f"[DRY RUN] 将删除: {file_path} ({file_size} bytes)")
                self.stats['bytes_saved'] += file_size
                return True
            
            # 创建备份（可选）
            backup_dir = file_path.parent / ".backup"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / file_path.name
            
            shutil.copy2(file_path, backup_path)
            logger.debug(f"已备份到: {backup_path}")
            
            # 删除原文件
            file_path.unlink()
            
            logger.info(f"已删除: {file_path} ({file_size} bytes)")
            self.stats['json_files_removed'] += 1
            self.stats['bytes_saved'] += file_size
            
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {file_path} - {e}")
            self.stats['errors'] += 1
            return False
    
    def cleanup_empty_directories(self) -> None:
        """清理空目录"""
        try:
            experiments_dir = self.storage_root / "experiments"
            
            for exp_dir in experiments_dir.iterdir():
                if not exp_dir.is_dir():
                    continue
                
                # 检查备份目录
                for backup_dir in exp_dir.rglob(".backup"):
                    if backup_dir.is_dir() and not any(backup_dir.iterdir()):
                        if self.dry_run:
                            logger.info(f"[DRY RUN] 将删除空备份目录: {backup_dir}")
                        else:
                            backup_dir.rmdir()
                            logger.info(f"已删除空备份目录: {backup_dir}")
                            
        except Exception as e:
            logger.error(f"清理空目录失败: {e}")
    
    def find_unused_code_patterns(self) -> List[str]:
        """查找可能未使用的代码模式"""
        patterns = []
        
        # 检查是否还有直接的JSON文件读取
        backend_dir = Path(__file__).parent.parent / "src"
        
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # 查找可能的遗留模式
                    if 'json.gz' in content and 'trajectory' in content:
                        patterns.append(f"可能的遗留轨迹JSON读取: {py_file}")
                    
                    if 'json.gz' in content and 'pr_curve' in content:
                        patterns.append(f"可能的遗留PR曲线JSON读取: {py_file}")
                        
                except Exception:
                    continue
        
        return patterns
    
    def cleanup_all(self, verify_integrity: bool = True) -> None:
        """执行完整清理"""
        logger.info("开始清理遗留文件...")
        
        # 查找遗留文件
        legacy_files = self.find_legacy_files()
        
        if not legacy_files:
            logger.info("没有发现可清理的文件")
            return
        
        # 删除遗留文件
        for file_path in legacy_files:
            if verify_integrity:
                self.remove_legacy_file(file_path)
            else:
                # 跳过完整性检查，直接删除
                try:
                    file_size = file_path.stat().st_size
                    if self.dry_run:
                        logger.info(f"[DRY RUN] 将删除: {file_path} ({file_size} bytes)")
                        self.stats['bytes_saved'] += file_size
                    else:
                        file_path.unlink()
                        logger.info(f"已删除: {file_path} ({file_size} bytes)")
                        self.stats['json_files_removed'] += 1
                        self.stats['bytes_saved'] += file_size
                except Exception as e:
                    logger.error(f"删除文件失败: {file_path} - {e}")
                    self.stats['errors'] += 1
        
        # 清理空目录
        self.cleanup_empty_directories()
        
        # 查找未使用的代码
        unused_patterns = self.find_unused_code_patterns()
        if unused_patterns:
            logger.info("发现可能未使用的代码模式:")
            for pattern in unused_patterns:
                logger.info(f"  - {pattern}")
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n" + "="*50)
        print("清理统计信息")
        print("="*50)
        print(f"发现JSON文件: {self.stats['json_files_found']}")
        print(f"删除JSON文件: {self.stats['json_files_removed']}")
        print(f"Arrow文件数量: {self.stats['arrow_files_found']}")
        print(f"节省空间: {self.stats['bytes_saved'] / 1024 / 1024:.2f} MB")
        print(f"错误数量: {self.stats['errors']}")
        print("="*50)


def main():
    parser = argparse.ArgumentParser(description="清理已迁移的遗留JSON文件")
    parser.add_argument("--storage-root", required=True, help="存储根目录路径")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要删除的内容，不实际执行")
    parser.add_argument("--skip-integrity-check", action="store_true", help="跳过Arrow文件完整性检查")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    storage_root = Path(args.storage_root)
    if not storage_root.exists():
        print(f"错误: 存储根目录不存在: {storage_root}")
        sys.exit(1)
    
    print(f"开始清理遗留文件...")
    print(f"存储根目录: {storage_root}")
    print(f"模式: {'预览模式' if args.dry_run else '实际清理'}")
    print(f"完整性检查: {'跳过' if args.skip_integrity_check else '启用'}")
    print()
    
    cleaner = LegacyCleaner(str(storage_root), dry_run=args.dry_run)
    
    try:
        cleaner.cleanup_all(verify_integrity=not args.skip_integrity_check)
        cleaner.print_stats()
        
        if args.dry_run:
            print("\n这是预览模式，没有实际删除任何文件。")
            print("要执行实际清理，请移除 --dry-run 参数。")
        else:
            print("\n清理完成！")
            print("备份文件保存在各目录的 .backup 子目录中。")
            
    except KeyboardInterrupt:
        print("\n清理被用户中断")
        cleaner.print_stats()
        sys.exit(1)
    except Exception as e:
        print(f"\n清理失败: {e}")
        cleaner.print_stats()
        sys.exit(1)


if __name__ == "__main__":
    main()
