#
# 功能: 实验数据清单管理器
#
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ManifestManager:
    """实验数据清单管理器
    
    负责生成和管理实验数据的清单文件，包含资源位置、大小、哈希等信息
    """
    
    def __init__(self, storage_root: Path):
        self.storage_root = Path(storage_root)
    
    def generate_manifest(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """生成实验数据清单"""
        try:
            manifest = {
                "version": 1,
                "experiment_id": experiment_id,
                "algorithm_key": algorithm_key,
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "trajectory": self._get_trajectory_info(experiment_id, algorithm_key),
                "pr_curve": self._get_pr_curve_info(experiment_id, algorithm_key),
                "frames": self._get_frames_info(experiment_id, algorithm_key),
            }
            
            return manifest
            
        except Exception as e:
            logger.error(f"生成清单失败: {e}")
            return self._create_empty_manifest(experiment_id, algorithm_key)
    
    def save_manifest(self, experiment_id: str, algorithm_key: str, manifest: Dict[str, Any]) -> None:
        """保存清单文件"""
        try:
            manifest_path = self.storage_root / f"experiments/{experiment_id}/manifests/{algorithm_key}.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"清单已保存: {manifest_path}")
            
        except Exception as e:
            logger.error(f"保存清单失败: {e}")
            raise
    
    def load_manifest(self, experiment_id: str, algorithm_key: str) -> Optional[Dict[str, Any]]:
        """加载清单文件"""
        try:
            manifest_path = self.storage_root / f"experiments/{experiment_id}/manifests/{algorithm_key}.json"
            
            if not manifest_path.exists():
                return None
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"加载清单失败: {e}")
            return None
    
    def _get_trajectory_info(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """获取轨迹数据信息"""
        info = {}
        
        # UI版本
        ui_path = self.storage_root / f"experiments/{experiment_id}/trajectories/{algorithm_key}.ui.arrow"
        if ui_path.exists():
            info["ui"] = self._get_file_info(ui_path, "arrow-ipc")
        
        # Full版本
        full_path = self.storage_root / f"experiments/{experiment_id}/trajectories/{algorithm_key}.arrow"
        if full_path.exists():
            info["full"] = self._get_file_info(full_path, "arrow-ipc")
            info["full"]["optional"] = True
        
        # 兼容JSON版本
        json_path = self.storage_root / f"experiments/{experiment_id}/trajectories/{algorithm_key}.json.gz"
        if json_path.exists():
            info["legacy"] = self._get_file_info(json_path, "json-gzip")
        
        return info
    
    def _get_pr_curve_info(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """获取PR曲线数据信息"""
        info = {}
        
        # UI版本
        ui_path = self.storage_root / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.ui.arrow"
        if ui_path.exists():
            info["ui"] = self._get_file_info(ui_path, "arrow-ipc")
            
            # 尝试读取元数据获取AUC等信息
            try:
                from .arrow_writer import ArrowReader
                reader = ArrowReader()
                pr_data = reader.read_pr_curve(ui_path)
                if pr_data and pr_data.get("metadata"):
                    metadata = pr_data["metadata"]
                    info["aux"] = {
                        "auc": float(metadata.get("auc_score", 0.0)),
                        "optimal_precision": float(metadata.get("optimal_precision", 0.0)),
                        "optimal_recall": float(metadata.get("optimal_recall", 0.0)),
                        "max_f1_score": float(metadata.get("max_f1_score", 0.0)),
                    }
            except Exception:
                pass
        
        # Full版本
        full_path = self.storage_root / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.arrow"
        if full_path.exists():
            info["full"] = self._get_file_info(full_path, "arrow-ipc")
            info["full"]["optional"] = True
        
        return info
    
    def _get_frames_info(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """获取帧数据信息"""
        info = {}
        
        # 批量帧文件
        batch_path = self.storage_root / f"experiments/{experiment_id}/frames/{algorithm_key}.json.gz"
        if batch_path.exists():
            info["batch"] = self._get_file_info(batch_path, "json-gzip")
        
        # 逐帧文件目录
        frames_dir = self.storage_root / f"experiments/{experiment_id}/frames/{algorithm_key}"
        if frames_dir.exists() and frames_dir.is_dir():
            frame_files = list(frames_dir.glob("*.json.gz"))
            if frame_files:
                info["individual"] = {
                    "count": len(frame_files),
                    "directory": f"/assets/experiments/{experiment_id}/frames/{algorithm_key}/",
                    "pattern": "{{frame_id:06d}}.json.gz"
                }
        
        return info
    
    def _get_file_info(self, path: Path, encoding: str, skip_hash: bool = False) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            stat = path.stat()

            # 计算文件哈希（可选，对大文件很慢）
            file_hash = "sha256:unknown"
            if not skip_hash and stat.st_size < 10 * 1024 * 1024:  # 只对小于10MB的文件计算哈希
                hash_sha256 = hashlib.sha256()
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
                file_hash = f"sha256:{hash_sha256.hexdigest()}"
            elif not skip_hash:
                # 对大文件，使用文件大小和修改时间作为简单标识
                file_hash = f"sha256:large_file_{stat.st_size}_{int(stat.st_mtime)}"

            # 尝试获取点数信息（对于Arrow文件）
            points = None
            if encoding == "arrow-ipc" and path.suffix == ".arrow":
                try:
                    import pyarrow.ipc as ipc
                    with ipc.open_file(path) as source:
                        table = source.read_all()
                        points = len(table)
                except Exception:
                    pass
            
            try:
                rel = path.relative_to(self.storage_root / 'experiments').as_posix()
                url = f"/assets/experiments/{rel}"
            except Exception:
                # 回退：相对 storage_root
                rel = path.relative_to(self.storage_root).as_posix() if path.is_absolute() else path.as_posix()
                url = f"/assets/experiments/{rel}"

            info = {
                "url": url,
                "bytes": stat.st_size,
                "hash": file_hash,
                "encoding": encoding,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
            if points is not None:
                info["points"] = points
            
            return info
            
        except Exception as e:
            logger.error(f"获取文件信息失败 {path}: {e}")
            # 当文件不在 experiments 子树时，退化为相对 storage_root 的 URL
            try:
                rel = path.relative_to(self.storage_root).as_posix()
                url = f"/assets/experiments/{rel}"
            except Exception:
                url = f"/assets/experiments/{path.name}"
            return {
                "url": url,
                "bytes": 0,
                "hash": "sha256:unknown",
                "encoding": encoding,
                "error": str(e)
            }
    
    def _create_empty_manifest(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """创建空清单"""
        return {
            "version": 1,
            "experiment_id": experiment_id,
            "algorithm_key": algorithm_key,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "trajectory": {},
            "pr_curve": {},
            "frames": {},
            "error": "Failed to generate manifest"
        }
    
    def update_manifest_after_save(self, experiment_id: str, algorithm_key: str) -> None:
        """在保存数据后更新清单"""
        try:
            manifest = self.generate_manifest(experiment_id, algorithm_key)
            self.save_manifest(experiment_id, algorithm_key, manifest)
        except Exception as e:
            logger.error(f"更新清单失败: {e}")


def create_manifest_manager(storage_root: str) -> ManifestManager:
    """创建清单管理器实例"""
    return ManifestManager(Path(storage_root))
