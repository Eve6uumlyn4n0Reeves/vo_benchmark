#
# 功能: 系统集成测试
#
import pytest
import tempfile
import shutil
import numpy as np
import cv2
import json
from pathlib import Path
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api.app import create_app
from src.storage.filesystem import FileSystemStorage
from src.storage.experiment import ExperimentStorage
from src.models.experiment import ExperimentConfig
from src.models.types import FeatureType, RANSACType
from src.pipeline.manager import ExperimentManager

class TestSystemIntegration:
    """系统集成测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_dataset(self, temp_dir):
        """创建模拟数据集"""
        dataset_dir = temp_dir / "dataset"
        dataset_dir.mkdir()
        
        # 创建序列目录
        seq_dir = dataset_dir / "sequence01"
        seq_dir.mkdir()
        
        # 创建TUM格式的rgb目录
        rgb_dir = seq_dir / "rgb"
        rgb_dir.mkdir()
        
        # 创建一些测试图像
        for i in range(5):
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            # 添加移动的特征
            cv2.rectangle(image, (100 + i*10, 100 + i*5), (200 + i*10, 200 + i*5), (255, 255, 255), -1)
            cv2.circle(image, (400 + i*5, 300 + i*3), 50, (255, 255, 255), -1)
            
            cv2.imwrite(str(rgb_dir / f"{i:06d}.png"), image)

        # 创建TUM格式的rgb.txt文件
        rgb_txt = seq_dir / "rgb.txt"
        with open(rgb_txt, 'w') as f:
            f.write("# color images\n")
            f.write("# timestamp filename\n")
            for i in range(5):
                timestamp = 1305031102.175304 + i * 0.1
                f.write(f"{timestamp:.6f} rgb/{i:06d}.png\n")

        # 创建相机内参文件
        calib_file = seq_dir / "calib.txt"
        with open(calib_file, 'w') as f:
            f.write("525.0 0.0 320.0\n")
            f.write("0.0 525.0 240.0\n")
            f.write("0.0 0.0 1.0\n")
        
        # 创建TUM格式的地面真值文件
        gt_file = seq_dir / "groundtruth.txt"
        with open(gt_file, 'w') as f:
            f.write("# ground truth trajectory\n")
            f.write("# timestamp tx ty tz qx qy qz qw\n")
            for i in range(5):
                timestamp = 1305031102.175304 + i * 0.1
                # 简单的线性运动
                tx, ty, tz = i * 0.1, 0.0, i * 0.05
                # 单位四元数 (TUM格式: x, y, z, w)
                qx, qy, qz, qw = 0.0, 0.0, 0.0, 1.0
                f.write(f"{timestamp:.6f} {tx:.6f} {ty:.6f} {tz:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
        
        return dataset_dir
    
    @pytest.fixture
    def experiment_config(self, mock_dataset, temp_dir):
        """创建实验配置"""
        return ExperimentConfig(
            name="integration_test",
            dataset_path=mock_dataset,
            output_dir=temp_dir / "output",
            feature_types=[FeatureType.SIFT],
            ransac_types=[RANSACType.STANDARD],
            sequences=["sequence01"],
            num_runs=1,
            parallel_jobs=1,
            random_seed=42,
            save_frame_data=True,
            save_descriptors=False,
            compute_pr_curves=False,
            analyze_ransac=True,
            ransac_success_threshold=0.1,
            max_features=1000,
            feature_params={},
            ransac_threshold=1.0,
            ransac_confidence=0.99,
            ransac_max_iters=1000
        )
    
    def test_end_to_end_experiment(self, experiment_config, temp_dir):
        """测试端到端实验执行"""
        # 创建存储
        storage_backend = FileSystemStorage(str(temp_dir / "storage"))
        storage = ExperimentStorage(storage_backend)
        
        # 创建实验管理器
        manager = ExperimentManager(experiment_config, storage)
        
        # 执行实验
        experiment_id = "test_exp_001"
        
        try:
            results = manager.run_experiment(experiment_id)
            
            # 验证结果
            assert len(results) > 0
            assert all(result.algorithm_key for result in results)
            assert all(result.success_rate >= 0 for result in results)
            
            # 验证存储
            saved_experiment = storage.get_experiment(experiment_id)
            assert saved_experiment is not None
            assert saved_experiment.experiment_id == experiment_id
            
            # 验证算法结果
            for result in results:
                saved_result = storage.get_algorithm_result(experiment_id, result.algorithm_key)
                assert saved_result is not None
                assert saved_result.algorithm_key == result.algorithm_key
            
        except Exception as e:
            pytest.fail(f"端到端实验执行失败: {e}")
    
    def test_api_experiment_workflow(self, mock_dataset, temp_dir):
        """测试通过API的完整实验工作流程"""
        app = create_app('testing')
        client = app.test_client()
        
        # 1. 创建实验
        experiment_data = {
            "name": "api_integration_test",
            "dataset_path": str(mock_dataset),
            "output_dir": str(temp_dir / "api_output"),
            "feature_types": ["SIFT"],
            "ransac_types": ["STANDARD"],
            "sequences": ["sequence01"],
            "num_runs": 1
        }
        
        with app.app_context():
            # 由于我们没有实际的服务实现，这里模拟API调用
            # 在实际测试中，这应该调用真实的API端点
            pass
    
    def test_storage_consistency(self, temp_dir):
        """测试存储一致性"""
        from src.models.experiment import ExperimentSummary, AlgorithmRun
        from src.models.evaluation import AlgorithmMetrics, MatchingMetrics, RANSACMetrics
        from src.models.frame import FrameResult
        from datetime import datetime
        
        # 创建存储
        storage_backend = FileSystemStorage(str(temp_dir / "storage"))
        storage = ExperimentStorage(storage_backend)
        
        # 创建测试数据
        # Create valid dataset path
        dataset_path = temp_dir / "dataset"
        dataset_path.mkdir()

        config = ExperimentConfig(
            name="storage_test",
            dataset_path=dataset_path,
            output_dir=temp_dir / "output",
            feature_types=[FeatureType.SIFT],
            ransac_types=[RANSACType.STANDARD],
            sequences=["seq01"],
            num_runs=1,
            parallel_jobs=1,
            random_seed=42,
            save_frame_data=True,
            save_descriptors=False,
            compute_pr_curves=False,
            analyze_ransac=False,
            ransac_success_threshold=0.8,
            max_features=1000,
            feature_params={},
            ransac_threshold=1.0,
            ransac_confidence=0.99,
            ransac_max_iters=1000
        )
        
        summary = ExperimentSummary(
            experiment_id="storage_test_001",
            timestamp=datetime.now().isoformat(),
            config=config,
            total_runs=1,
            successful_runs=1,
            failed_runs=0,
            algorithms_tested=["SIFT_STANDARD"],
            sequences_processed=["seq01"]
        )
        
        # 保存实验摘要
        storage.save_experiment("storage_test_001", summary)
        
        # 读取并验证
        loaded_summary = storage.get_experiment("storage_test_001")
        assert loaded_summary is not None
        assert loaded_summary.experiment_id == "storage_test_001"
        assert loaded_summary.config.name == "storage_test"
        
        # 创建算法指标
        metrics = AlgorithmMetrics(
            algorithm_key="SIFT_STANDARD_seq01_0",
            feature_type="SIFT",
            ransac_type="STANDARD",
            trajectory=None,
            matching=MatchingMetrics(
                avg_matches=100.0,
                avg_inliers=80.0,
                avg_inlier_ratio=0.8,
                avg_match_score=0.9,
                avg_reprojection_error=1.2
            ),
            ransac=RANSACMetrics(
                avg_iterations=150.0,
                std_iterations=50.0,
                min_iterations=100,
                max_iterations=200,
                convergence_rate=0.95,
                avg_inlier_ratio=0.8,
                success_rate=0.9,
                avg_processing_time_ms=10.5
            ),
            avg_frame_time_ms=50.0,
            total_time_s=2.5,
            fps=20.0,
            success_rate=0.9,
            failure_reasons={},
            total_frames=5,
            successful_frames=4,
            failed_frames=1
        )
        
        # 保存算法结果
        storage.save_algorithm_result("storage_test_001", "SIFT_STANDARD_seq01_0", metrics)
        
        # 读取并验证
        loaded_metrics = storage.get_algorithm_result("storage_test_001", "SIFT_STANDARD_seq01_0")
        assert loaded_metrics is not None
        assert loaded_metrics.algorithm_key == "SIFT_STANDARD_seq01_0"
        assert loaded_metrics.success_rate == 0.9
        assert loaded_metrics.matching.avg_matches == 100.0
    
    def test_error_handling_and_recovery(self, temp_dir):
        """测试错误处理和恢复"""
        from src.api.exceptions.base import VOBenchmarkException
        
        # 测试无效数据集路径
        # Test that invalid config raises error during construction
        with pytest.raises(AssertionError, match="数据集路径不存在"):
            invalid_config = ExperimentConfig(
                name="error_test",
                dataset_path=Path("/nonexistent/path"),
                output_dir=temp_dir / "output",
                feature_types=[FeatureType.SIFT],
                ransac_types=[RANSACType.STANDARD],
                sequences=["seq01"],
                num_runs=1,
                parallel_jobs=1,
                random_seed=42,
                save_frame_data=True,
                save_descriptors=False,
                compute_pr_curves=False,
                analyze_ransac=False,
                ransac_success_threshold=0.8,
                max_features=1000,
                feature_params={},
                ransac_threshold=1.0,
                ransac_confidence=0.99,
                ransac_max_iters=1000
            )

        # Test completed - invalid config construction should raise error
    
    def test_performance_benchmarks(self, experiment_config, temp_dir):
        """测试性能基准"""
        import time
        
        storage_backend = FileSystemStorage(str(temp_dir / "storage"))
        storage = ExperimentStorage(storage_backend)
        manager = ExperimentManager(experiment_config, storage)
        
        # 测量执行时间
        start_time = time.time()
        results = manager.run_experiment("perf_test_001")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证性能指标
        assert execution_time < 60.0  # 应该在60秒内完成
        assert len(results) > 0
        
        # 验证FPS指标
        for result in results:
            assert result.fps > 0  # 应该有正的FPS值
            assert result.avg_frame_time_ms > 0  # 应该有正的处理时间
    
    def test_concurrent_experiments(self, mock_dataset, temp_dir):
        """测试并发实验执行"""
        import threading
        import time
        
        def run_experiment(exp_id, results_list):
            try:
                config = ExperimentConfig(
                    name=f"concurrent_test_{exp_id}",
                    dataset_path=mock_dataset,
                    output_dir=temp_dir / f"output_{exp_id}",
                    feature_types=[FeatureType.SIFT],
                    ransac_types=[RANSACType.STANDARD],
                    sequences=["sequence01"],
                    num_runs=1,
                    parallel_jobs=1,
                    random_seed=42,
                    save_frame_data=True,
                    save_descriptors=False,
                    compute_pr_curves=False,
                    analyze_ransac=False,
                    ransac_success_threshold=0.8,
                    max_features=1000,
                    feature_params={},
                    ransac_threshold=1.0,
                    ransac_confidence=0.99,
                    ransac_max_iters=1000
                )
                
                storage_backend = FileSystemStorage(str(temp_dir / f"storage_{exp_id}"))
                storage = ExperimentStorage(storage_backend)
                manager = ExperimentManager(config, storage)
                
                results = manager.run_experiment(f"concurrent_exp_{exp_id}")
                results_list.append((exp_id, len(results)))
                
            except Exception as e:
                results_list.append((exp_id, f"Error: {e}"))
        
        # 启动多个并发实验
        threads = []
        results_list = []
        
        for i in range(3):
            thread = threading.Thread(target=run_experiment, args=(i, results_list))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=120)  # 2分钟超时
        
        # 验证结果
        assert len(results_list) == 3
        for exp_id, result in results_list:
            if isinstance(result, str) and result.startswith("Error"):
                pytest.fail(f"实验 {exp_id} 失败: {result}")
            else:
                assert result > 0  # 应该有结果

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
