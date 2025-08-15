#
# 功能: 增强的测试覆盖
#
import pytest
import numpy as np
import tempfile
import shutil
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.error_handling import (
    retry_on_failure, 
    FeatureExtractionError,
    safe_execute,
    validate_input,
    is_not_none,
    is_positive
)
from src.utils.performance import (
    FeatureCache,
    LRUCache,
    ParallelProcessor,
    performance_monitor
)
from src.storage.filesystem import FileSystemStorage
from src.core.features.sift import SIFTExtractor

class TestErrorHandling:
    """错误处理测试"""
    
    def test_retry_decorator_success(self):
        """测试重试装饰器 - 成功情况"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("临时错误")
            return "成功"
        
        result = flaky_function()
        assert result == "成功"
        assert call_count == 3
    
    def test_retry_decorator_failure(self):
        """测试重试装饰器 - 失败情况"""
        call_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("持续错误")
        
        with pytest.raises(ValueError, match="持续错误"):
            always_fail()
        assert call_count == 3  # 初始调用 + 2次重试
    
    def test_safe_execute_success(self):
        """测试安全执行 - 成功情况"""
        def success_func(x, y):
            return x + y
        
        result = safe_execute(success_func, 2, 3)
        assert result == 5
    
    def test_safe_execute_failure(self):
        """测试安全执行 - 失败情况"""
        def fail_func():
            raise ValueError("测试错误")
        
        result = safe_execute(fail_func, default_return="默认值")
        assert result == "默认值"
    
    def test_input_validation(self):
        """测试输入验证"""
        # 成功验证
        validate_input(5, [is_not_none, is_positive])
        
        # 失败验证
        with pytest.raises(ValueError):
            validate_input(None, [is_not_none])
        
        with pytest.raises(ValueError):
            validate_input(-1, [is_positive])

class TestPerformanceOptimization:
    """性能优化测试"""
    
    def test_lru_cache_basic(self):
        """测试LRU缓存基本功能"""
        cache = LRUCache(max_size=3)
        
        # 添加项目
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size() == 3
    
    def test_lru_cache_eviction(self):
        """测试LRU缓存淘汰机制"""
        cache = LRUCache(max_size=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # 应该淘汰key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_feature_cache(self):
        """测试特征缓存"""
        cache = FeatureCache(max_size=5)
        
        # 创建测试图像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        features = {"keypoints": [(10, 20), (30, 40)], "descriptors": np.random.rand(2, 128)}
        
        # 存储特征
        cache.store_features(image, "SIFT", features)
        
        # 获取特征
        cached_features = cache.get_features(image, "SIFT")
        assert cached_features is not None
        assert len(cached_features["keypoints"]) == 2
        
        # 测试缓存命中率
        assert cache.get_hit_rate() > 0
    
    def test_parallel_processor(self):
        """测试并行处理器"""
        def square(x):
            return x * x
        
        with ParallelProcessor(max_workers=2) as processor:
            results = processor.map(square, [1, 2, 3, 4, 5])
        
        assert results == [1, 4, 9, 16, 25]
    
    def test_performance_monitor(self):
        """测试性能监控器"""
        performance_monitor.clear()
        
        # 记录指标
        performance_monitor.record_metric("test_metric", 100.0, "ms")
        performance_monitor.record_metric("test_metric", 200.0, "ms")
        
        # 获取统计
        stats = performance_monitor.get_stats("test_metric")
        assert stats is not None
        assert stats["count"] == 2
        assert stats["mean"] == 150.0

class TestStorageSystem:
    """存储系统测试"""
    
    @pytest.fixture
    def temp_storage(self):
        """临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        storage = FileSystemStorage(temp_dir, enable_compression=True, enable_backup=True)
        yield storage
        shutil.rmtree(temp_dir)
    
    def test_json_storage(self, temp_storage):
        """测试JSON存储"""
        data = {"test": "data", "number": 42}
        
        temp_storage.save("test_json", data)
        loaded_data = temp_storage.load("test_json")
        
        assert loaded_data == data
        assert temp_storage.exists("test_json")
    
    def test_binary_storage(self, temp_storage):
        """测试二进制存储"""
        data = {"array": np.random.rand(10, 10), "text": "test"}
        
        temp_storage.save("test_binary", data)
        loaded_data = temp_storage.load("test_binary")
        
        assert isinstance(loaded_data["array"], np.ndarray)
        assert loaded_data["text"] == "test"
        np.testing.assert_array_equal(loaded_data["array"], data["array"])
    
    def test_compression(self, temp_storage):
        """测试压缩功能"""
        large_data = {"large_array": np.random.rand(1000, 1000)}
        
        # 保存压缩数据
        temp_storage.save("test_compressed", large_data, compress=True)
        
        # 保存未压缩数据
        temp_storage.save("test_uncompressed", large_data, compress=False)
        
        # 验证都能正确加载
        compressed_data = temp_storage.load("test_compressed")
        uncompressed_data = temp_storage.load("test_uncompressed")
        
        np.testing.assert_array_equal(
            compressed_data["large_array"], 
            uncompressed_data["large_array"]
        )
    
    def test_concurrent_access(self, temp_storage):
        """测试并发访问"""
        def write_data(key, value):
            temp_storage.save(f"concurrent_{key}", {"value": value})
        
        def read_data(key):
            return temp_storage.load(f"concurrent_{key}")
        
        # 并发写入
        threads = []
        for i in range(10):
            thread = threading.Thread(target=write_data, args=(i, i * 10))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 验证数据
        for i in range(10):
            data = read_data(i)
            assert data["value"] == i * 10
    
    def test_storage_info(self, temp_storage):
        """测试存储信息"""
        # 保存一些数据
        temp_storage.save("info_test1", {"data": "test1"})
        temp_storage.save("info_test2", {"data": "test2"})
        
        info = temp_storage.get_storage_info()
        
        assert info["file_count"] >= 2
        assert info["total_size_bytes"] > 0
        assert "backup_enabled" in info

class TestBoundaryConditions:
    """边界条件测试"""
    
    def test_empty_image_handling(self):
        """测试空图像处理"""
        extractor = SIFTExtractor()
        
        # 测试None图像
        with pytest.raises(ValueError):
            extractor.extract(None)
        
        # 测试空数组
        empty_image = np.array([])
        result = extractor.extract(empty_image)
        assert len(result.keypoints) == 0
    
    def test_invalid_image_formats(self):
        """测试无效图像格式"""
        extractor = SIFTExtractor()
        
        # 测试1D数组
        invalid_image = np.random.rand(100)
        with pytest.raises(ValueError):
            extractor.extract(invalid_image)
        
        # 测试4D数组
        invalid_image = np.random.rand(10, 10, 3, 2)
        with pytest.raises(ValueError):
            extractor.extract(invalid_image)
    
    def test_extreme_values(self):
        """测试极值处理"""
        cache = LRUCache(max_size=1)
        
        # 测试最小缓存大小
        cache.put("key1", "value1")
        cache.put("key2", "value2")  # 应该淘汰key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        
        # 测试零大小缓存
        zero_cache = LRUCache(max_size=0)
        zero_cache.put("key", "value")
        assert zero_cache.get("key") is None

class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    def test_feature_extraction_performance(self):
        """测试特征提取性能"""
        extractor = SIFTExtractor()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start_time = time.time()
        features = extractor.extract(image)
        duration = time.time() - start_time
        
        # 特征提取应该在合理时间内完成（例如1秒）
        assert duration < 1.0
        assert len(features.keypoints) > 0
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache = FeatureCache(max_size=100)
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        features = {"test": "data"}
        
        # 测试存储性能
        start_time = time.time()
        for i in range(100):
            cache.store_features(image, f"extractor_{i}", features)
        store_duration = time.time() - start_time
        
        # 测试检索性能
        start_time = time.time()
        for i in range(100):
            cache.get_features(image, f"extractor_{i}")
        retrieve_duration = time.time() - start_time
        
        # 缓存操作应该很快
        assert store_duration < 0.1
        assert retrieve_duration < 0.1
    
    def test_storage_performance(self):
        """测试存储性能"""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = FileSystemStorage(temp_dir)
            data = {"array": np.random.rand(100, 100)}
            
            # 测试写入性能
            start_time = time.time()
            for i in range(10):
                storage.save(f"perf_test_{i}", data)
            write_duration = time.time() - start_time
            
            # 测试读取性能
            start_time = time.time()
            for i in range(10):
                storage.load(f"perf_test_{i}")
            read_duration = time.time() - start_time
            
            # 存储操作应该在合理时间内完成
            assert write_duration < 1.0
            assert read_duration < 0.5
            
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
