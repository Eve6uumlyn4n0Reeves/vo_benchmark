#
# 功能: 实现文件系统存储后端。
#
from typing import Any, List, Optional, Union, Dict
from pathlib import Path
import json
import pickle
import gzip
import threading
import shutil
import logging
import os
from datetime import datetime
from .base import Storage

logger = logging.getLogger(__name__)


class FileSystemStorage(Storage):
    """增强的文件系统存储，支持二进制数据、压缩、并发控制和备份"""

    def __init__(
        self, root_dir: str, enable_compression: bool = True, enable_backup: bool = True
    ):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.enable_compression = enable_compression
        self.enable_backup = enable_backup
        self._locks: Dict[str, threading.RLock] = {}  # 文件级锁
        self._global_lock = threading.RLock()

        # 创建备份目录
        if self.enable_backup:
            self.backup_dir = self.root_dir / "backups"
            self.backup_dir.mkdir(exist_ok=True)

    def _get_lock(self, key: str) -> threading.RLock:
        """获取文件级锁"""
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.RLock()
            return self._locks[key]

    def _path_with_compression(
        self, key: str, is_binary: bool, use_compression: bool
    ) -> Path:
        """根据是否压缩返回正确的文件路径扩展名"""
        if is_binary:
            extension = ".pkl.gz" if use_compression else ".pkl"
        else:
            extension = ".json.gz" if use_compression else ".json"
        return self.root_dir / f"{key}{extension}"

    def _get_path(self, key: str, is_binary: bool = False) -> Path:
        """获取文件路径（保留向后兼容，基于默认配置）"""
        return self._path_with_compression(key, is_binary, self.enable_compression)

    def _create_backup(self, path: Path) -> None:
        """创建文件备份"""
        if not self.enable_backup or not path.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}_{timestamp}{path.suffix}"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(path, backup_path)

            # 清理旧备份（保留最近5个）
            self._cleanup_old_backups(path.stem)
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")

    def _cleanup_old_backups(self, key: str) -> None:
        """清理旧备份文件"""
        try:
            pattern = f"{key}_*"
            backup_files = sorted(
                self.backup_dir.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            # 保留最近5个备份
            for old_backup in backup_files[5:]:
                old_backup.unlink()
        except Exception as e:
            logger.warning(f"清理备份失败: {e}")

    def save(self, key: str, data: Any, compress: Optional[bool] = None) -> None:
        """保存数据，自动检测数据类型并选择合适的序列化方式"""
        lock = self._get_lock(key)
        with lock:
            # 确定是否使用压缩
            use_compression = (
                compress if compress is not None else self.enable_compression
            )

            # 检测数据类型并选择与压缩一致的路径
            is_binary = self._is_binary_data(data)
            path = self._path_with_compression(key, is_binary, use_compression)

            # 创建备份
            self._create_backup(path)

            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            try:
                if is_binary:
                    self._save_binary(path, data, use_compression)
                else:
                    self._save_json(path, data, use_compression)

                logger.debug(f"保存数据到 {path}")
            except Exception as e:
                logger.error(f"保存数据失败 {key}: {e}")
                raise

    def _is_binary_data(self, data: Any) -> bool:
        """检测是否为二进制数据"""
        import numpy as np

        # 检查是否包含NumPy数组或其他二进制数据
        if isinstance(data, np.ndarray):
            return True
        elif isinstance(data, dict):
            return any(isinstance(v, np.ndarray) for v in data.values())
        elif isinstance(data, (list, tuple)):
            return any(isinstance(item, np.ndarray) for item in data)
        elif hasattr(data, "__dict__"):
            return any(isinstance(v, np.ndarray) for v in data.__dict__.values())

        return False

    def _save_binary(self, path: Path, data: Any, use_compression: bool) -> None:
        """保存二进制数据"""
        if use_compression:
            with gzip.open(path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _save_json(self, path: Path, data: Any, use_compression: bool) -> None:
        """保存JSON数据（原子写入，先写临时文件再rename覆盖）"""
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # 原子写入策略：写入 .tmp 再替换
        tmp_path = Path(str(path) + ".tmp")
        if use_compression:
            with gzip.open(tmp_path, "wt", encoding="utf-8") as f:
                f.write(json_str)
        else:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        # Windows 上使用 replace 也能尽量保证原子性
        try:
            os.replace(tmp_path, path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def load(self, key: str) -> Optional[Any]:
        """加载数据，自动检测文件类型"""
        lock = self._get_lock(key)
        with lock:
            # 尝试不同的文件扩展名
            possible_paths = [
                self._get_path(key, is_binary=True),  # .pkl.gz 或 .pkl
                self._get_path(key, is_binary=False),  # .json.gz 或 .json
            ]

            # 如果启用了压缩，也尝试未压缩的版本
            if self.enable_compression:
                possible_paths.extend(
                    [self.root_dir / f"{key}.pkl", self.root_dir / f"{key}.json"]
                )

            for path in possible_paths:
                if path.exists():
                    try:
                        return self._load_file(path)
                    except Exception as e:
                        logger.warning(f"加载文件失败 {path}: {e}")
                        continue

            return None

    def _load_file(self, path: Path) -> Any:
        """根据文件扩展名加载文件"""
        if path.suffix == ".gz":
            # 压缩文件
            if ".pkl" in path.name:
                with gzip.open(path, "rb") as f:
                    return pickle.load(f)
            elif ".json" in path.name:
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    return json.load(f)
        else:
            # 未压缩文件
            if path.suffix == ".pkl":
                with open(path, "rb") as f:
                    return pickle.load(f)
            elif path.suffix == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)

        raise ValueError(f"不支持的文件格式: {path}")

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        possible_paths = [
            self._get_path(key, is_binary=True),
            self._get_path(key, is_binary=False),
        ]

        if self.enable_compression:
            possible_paths.extend(
                [self.root_dir / f"{key}.pkl", self.root_dir / f"{key}.json"]
            )

        return any(path.exists() for path in possible_paths)

    def delete(self, key: str) -> bool:
        """删除键对应的所有文件"""
        lock = self._get_lock(key)
        with lock:
            deleted = False
            possible_paths = [
                self._get_path(key, is_binary=True),
                self._get_path(key, is_binary=False),
                self.root_dir / f"{key}.pkl",
                self.root_dir / f"{key}.json",
            ]

            for path in possible_paths:
                if path.exists():
                    try:
                        # 创建备份
                        self._create_backup(path)
                        path.unlink()
                        deleted = True
                        logger.debug(f"删除文件: {path}")
                    except Exception as e:
                        logger.error(f"删除文件失败 {path}: {e}")

            return deleted

    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键（递归扫描，返回相对于 root_dir 的相对键，包含子目录）。
        例如：保存 key="experiments/exp123/summary"，会返回同样的相对键。
        """
        keys: set[str] = set()

        # 规范化前缀，允许空/带斜杠/不带斜杠
        norm_prefix = prefix.strip("/")
        base = self.root_dir / norm_prefix if norm_prefix else self.root_dir

        # 递归扫描所有支持的扩展名
        patterns = [
            "**/*.json",
            "**/*.json.gz",
            "**/*.pkl",
            "**/*.pkl.gz",
        ]

        for pattern in patterns:
            for path in base.rglob(pattern):
                # 计算相对路径作为键基础
                rel = path.relative_to(self.root_dir).as_posix()
                # 去除扩展名（先去 .gz 再去 .json/.pkl）
                if rel.endswith(".gz"):
                    rel = rel[:-3]
                if rel.endswith(".json") or rel.endswith(".pkl"):
                    rel = rel.rsplit(".", 1)[0]
                keys.add(rel)

        # 仅返回匹配前缀的键（确保以 norm_prefix 开头）
        if norm_prefix:
            keys = {
                k for k in keys if k.startswith(norm_prefix + "/") or k == norm_prefix
            }

        return sorted(keys)

    def get_storage_info(self) -> dict:
        """获取存储信息"""
        total_size = 0
        file_count = 0

        for path in self.root_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
                file_count += 1

        backup_size = 0
        backup_count = 0
        if self.enable_backup and self.backup_dir.exists():
            for path in self.backup_dir.rglob("*"):
                if path.is_file():
                    backup_size += path.stat().st_size
                    backup_count += 1

        return {
            "root_dir": str(self.root_dir),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "backup_enabled": self.enable_backup,
            "backup_size_bytes": backup_size,
            "backup_size_mb": round(backup_size / (1024 * 1024), 2),
            "backup_count": backup_count,
            "compression_enabled": self.enable_compression,
        }
