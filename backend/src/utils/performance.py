#
# 功能: 性能优化工具
#
import time
import hashlib
import threading
import functools
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Union, List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


class LRUCache:
    """线程安全的LRU缓存"""

    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                # 更新访问顺序
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return None

    def put(self, key: str, value: Any) -> None:
        """存储缓存值"""
        with self.lock:
            if self.max_size <= 0:
                # 边界条件：不缓存，直接返回
                return
            if key in self.cache:
                # 更新现有值
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # 移除最久未使用的项（确保访问顺序非空）
                if self.access_order:
                    oldest_key = self.access_order.pop(0)
                    del self.cache[oldest_key]

            self.cache[key] = value
            self.access_order.append(key)

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "usage_ratio": len(self.cache) / self.max_size,
            }


class FeatureCache:
    """特征缓存管理器"""

    def __init__(self, max_size: int = 100):
        self.cache = LRUCache(max_size)
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()

    def _compute_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希值（健壮处理None和非二维/三维数组）"""
        if image is None:
            return "none"
        try:
            shape_str = str(image.shape)
            if image.ndim == 1:
                sample = image.flatten()[:100]
            elif image.ndim >= 2:
                sample = image[::10, ::10].flatten()[:100]
            else:
                sample = np.array([], dtype=np.uint8)
            content = shape_str + str(sample.tobytes())
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            # 最终兜底，避免缓存计算影响主流程
            return str(id(image))

    def get_features(self, image: np.ndarray, extractor_name: str) -> Optional[Any]:
        """获取缓存的特征"""
        image_hash = self._compute_image_hash(image)
        cache_key = f"{extractor_name}_{image_hash}"

        with self.lock:
            features = self.cache.get(cache_key)
            if features is not None:
                self.hit_count += 1
                logger.debug(f"特征缓存命中: {cache_key}")
                return features
            else:
                self.miss_count += 1
                return None

    def store_features(
        self, image: np.ndarray, extractor_name: str, features: Any
    ) -> None:
        """存储特征到缓存"""
        image_hash = self._compute_image_hash(image)
        cache_key = f"{extractor_name}_{image_hash}"

        with self.lock:
            self.cache.put(cache_key, features)
            logger.debug(f"特征已缓存: {cache_key}")

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.get_hit_rate(),
            "cache_stats": self.cache.get_stats(),
        }

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0


# 全局特征缓存实例
feature_cache = FeatureCache()


def cached_feature_extraction(extractor_name: str):
    """特征提取缓存装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, image: np.ndarray, *args, **kwargs):
            # 尝试从缓存获取
            cached_features = feature_cache.get_features(image, extractor_name)
            if cached_features is not None:
                return cached_features

            # 缓存未命中，执行特征提取
            features = func(self, image, *args, **kwargs)

            # 存储到缓存
            feature_cache.store_features(image, extractor_name, features)

            return features

        return wrapper

    return decorator


class ParallelProcessor:
    """并行处理器"""

    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.executor = None

    def __enter__(self):
        if self.use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown(wait=True)

    def map(self, func: Callable, iterable, timeout: Optional[float] = None):
        """并行映射函数"""
        if self.executor is None:
            raise RuntimeError("ParallelProcessor must be used as context manager")

        futures = [self.executor.submit(func, item) for item in iterable]
        results = []

        for future in futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                logger.error(f"并行处理任务失败: {e}")
                results.append(None)

        return results


def profile_performance(func: Callable) -> Callable:
    """性能分析装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = _get_memory_usage()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            end_time = time.time()
            end_memory = _get_memory_usage()

            duration = end_time - start_time
            memory_delta = end_memory - start_memory

            logger.info(
                f"性能分析 {func.__name__}: "
                f"耗时={duration:.3f}s, "
                f"内存变化={memory_delta:.1f}MB, "
                f"成功={success}"
            )

        return result

    return wrapper


def _get_memory_usage() -> float:
    """获取当前内存使用量（MB）"""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def batch_process(batch_size: int = 32):
    """批处理装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items, *args, **kwargs):
            if not isinstance(items, (list, tuple)):
                return func(items, *args, **kwargs)

            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                batch_results = [func(item, *args, **kwargs) for item in batch]
                results.extend(batch_results)

            return results

        return wrapper

    return decorator


def memory_efficient_copy(array: np.ndarray) -> np.ndarray:
    """内存高效的数组拷贝"""
    if array.flags.c_contiguous:
        return array.copy()
    else:
        # 对于非连续数组，先重新排列再拷贝
        return np.ascontiguousarray(array)


def optimize_image_processing(image: np.ndarray) -> np.ndarray:
    """优化图像处理"""
    # 确保图像是连续的内存布局
    if not image.flags.c_contiguous:
        image = np.ascontiguousarray(image)

    # 确保数据类型正确（仅当有有效尺寸时）
    if image.size > 0 and image.dtype != np.uint8:
        max_val = float(image.max()) if hasattr(image, "max") else 0.0
        if max_val <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)

    return image


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {}
        self.lock = threading.RLock()

    def record_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """记录性能指标"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = {"values": [], "unit": unit}
            self.metrics[name]["values"].append(value)

    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """获取指标统计"""
        with self.lock:
            if name not in self.metrics:
                return None

            values = self.metrics[name]["values"]
            if not values:
                return None

            return {
                "count": len(values),
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values),
                "unit": self.metrics[name]["unit"],
            }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标统计"""
        with self.lock:
            # 过滤 None，保证返回值类型稳定
            result: Dict[str, Dict[str, float]] = {}
            for name in self.metrics.keys():
                stats = self.get_stats(name)
                if stats is not None:
                    result[name] = stats
            return result

    def clear(self) -> None:
        """清空所有指标"""
        with self.lock:
            self.metrics.clear()


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
