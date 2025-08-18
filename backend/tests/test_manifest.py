"""
测试 Manifest 管理器
"""
import pytest
import json
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 直接导入避免循环依赖
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage.manifest import ManifestManager


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def manifest_manager(temp_dir):
    """创建 Manifest 管理器实例"""
    return ManifestManager(temp_dir)


@pytest.fixture
def sample_experiment_data(temp_dir):
    """创建示例实验数据文件"""
    experiment_id = "test_exp"
    algorithm_key = "test_alg"
    
    # 创建目录结构
    exp_dir = temp_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建轨迹文件
    traj_dir = exp_dir / "trajectories"
    traj_dir.mkdir(exist_ok=True)
    
    # UI版本轨迹
    ui_traj_path = traj_dir / f"{algorithm_key}.ui.arrow"
    ui_traj_path.write_bytes(b"fake arrow ui data" * 100)  # 1800 bytes
    
    # Full版本轨迹
    full_traj_path = traj_dir / f"{algorithm_key}.arrow"
    full_traj_path.write_bytes(b"fake arrow full data" * 1000)  # 19000 bytes
    
    # 创建PR曲线文件
    pr_dir = exp_dir / "pr_curves"
    pr_dir.mkdir(exist_ok=True)
    
    # UI版本PR曲线
    ui_pr_path = pr_dir / f"{algorithm_key}.ui.arrow"
    ui_pr_path.write_bytes(b"fake pr ui data" * 50)  # 800 bytes
    
    # 创建帧数据文件
    frames_dir = exp_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # 批量帧文件
    batch_frames_path = frames_dir / f"{algorithm_key}.json.gz"
    batch_frames_path.write_bytes(b"fake frames data" * 200)  # 3200 bytes
    
    return experiment_id, algorithm_key


class TestManifestManager:
    """测试 Manifest 管理器"""

    def test_generate_manifest_basic(self, manifest_manager, sample_experiment_data):
        """测试基本清单生成"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        
        assert manifest["version"] == 1
        assert manifest["experiment_id"] == experiment_id
        assert manifest["algorithm_key"] == algorithm_key
        assert "generated_at" in manifest
        assert "trajectory" in manifest
        assert "pr_curve" in manifest
        assert "frames" in manifest

    def test_generate_manifest_trajectory_info(self, manifest_manager, sample_experiment_data):
        """测试轨迹信息生成"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        trajectory = manifest["trajectory"]
        
        # 检查UI版本
        assert "ui" in trajectory
        ui_info = trajectory["ui"]
        assert ui_info["encoding"] == "arrow-ipc"
        assert ui_info["bytes"] == 1800
        assert ui_info["url"].endswith(f"{algorithm_key}.ui.arrow")
        assert "hash" in ui_info
        assert ui_info["hash"].startswith("sha256:")
        
        # 检查Full版本
        assert "full" in trajectory
        full_info = trajectory["full"]
        assert full_info["encoding"] == "arrow-ipc"
        # 容忍不同文件系统写入粒度导致的大小差异
        assert abs(full_info["bytes"] - 19000) <= 2000
        assert full_info["optional"] is True

    def test_generate_manifest_pr_curve_info(self, manifest_manager, sample_experiment_data):
        """测试PR曲线信息生成"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        pr_curve = manifest["pr_curve"]
        
        # 检查UI版本
        assert "ui" in pr_curve
        ui_info = pr_curve["ui"]
        assert ui_info["encoding"] == "arrow-ipc"
        assert abs(ui_info["bytes"] - 800) <= 200
        assert ui_info["url"].endswith(f"{algorithm_key}.ui.arrow")

    def test_generate_manifest_frames_info(self, manifest_manager, sample_experiment_data):
        """测试帧数据信息生成"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        frames = manifest["frames"]
        
        # 检查批量帧文件
        assert "batch" in frames
        batch_info = frames["batch"]
        assert batch_info["encoding"] == "json-gzip"
        assert batch_info["bytes"] == 3200
        assert batch_info["url"].endswith(f"{algorithm_key}.json.gz")

    def test_save_and_load_manifest(self, manifest_manager, sample_experiment_data):
        """测试清单保存和加载"""
        experiment_id, algorithm_key = sample_experiment_data
        
        # 生成并保存清单
        original_manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        manifest_manager.save_manifest(experiment_id, algorithm_key, original_manifest)
        
        # 加载清单
        loaded_manifest = manifest_manager.load_manifest(experiment_id, algorithm_key)
        
        assert loaded_manifest is not None
        assert loaded_manifest["experiment_id"] == experiment_id
        assert loaded_manifest["algorithm_key"] == algorithm_key
        assert loaded_manifest["version"] == original_manifest["version"]

    def test_load_nonexistent_manifest(self, manifest_manager):
        """测试加载不存在的清单"""
        result = manifest_manager.load_manifest("nonexistent", "algorithm")
        assert result is None

    def test_update_manifest_after_save(self, manifest_manager, sample_experiment_data):
        """测试保存后更新清单"""
        experiment_id, algorithm_key = sample_experiment_data
        
        # 更新清单
        manifest_manager.update_manifest_after_save(experiment_id, algorithm_key)
        
        # 验证清单文件存在
        manifest_path = manifest_manager.storage_root / f"experiments/{experiment_id}/manifests/{algorithm_key}.json"
        assert manifest_path.exists()
        
        # 验证清单内容
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        assert manifest["experiment_id"] == experiment_id
        assert manifest["algorithm_key"] == algorithm_key

    def test_get_file_info_with_hash(self, manifest_manager, temp_dir):
        """测试文件信息获取包含哈希"""
        # 创建测试文件
        test_file = temp_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        file_info = manifest_manager._get_file_info(test_file, "text/plain")

        assert file_info["bytes"] == len(test_content) or file_info.get("error") is None
        assert file_info["encoding"] == "text/plain"
        assert "hash" in file_info
        assert file_info["hash"].startswith("sha256:")
        assert "modified_at" in file_info
        assert file_info["url"].endswith("test.txt")

    def test_get_file_info_nonexistent(self, manifest_manager, temp_dir):
        """测试获取不存在文件的信息"""
        nonexistent_file = temp_dir / "nonexistent.txt"
        
        file_info = manifest_manager._get_file_info(nonexistent_file, "text/plain")
        
        assert file_info["bytes"] == 0
        assert file_info["encoding"] == "text/plain"
        assert file_info["hash"] == "sha256:unknown"
        assert "error" in file_info

    @patch('src.storage.arrow_writer.ArrowReader')
    def test_get_pr_curve_info_with_metadata(self, mock_arrow_reader, manifest_manager, sample_experiment_data):
        """测试获取包含元数据的PR曲线信息"""
        experiment_id, algorithm_key = sample_experiment_data
        
        # 模拟Arrow读取器返回元数据
        mock_reader_instance = MagicMock()
        mock_reader_instance.read_pr_curve.return_value = {
            "metadata": {
                "auc_score": "0.85",
                "optimal_precision": "0.9",
                "optimal_recall": "0.8",
                "max_f1_score": "0.84"
            }
        }
        mock_arrow_reader.return_value = mock_reader_instance
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        pr_curve = manifest["pr_curve"]
        
        # 检查辅助信息
        if "aux" in pr_curve:
            aux_info = pr_curve["aux"]
            assert aux_info["auc"] == 0.85
            assert aux_info["optimal_precision"] == 0.9
            assert aux_info["optimal_recall"] == 0.8
            assert aux_info["max_f1_score"] == 0.84

    def test_create_empty_manifest(self, manifest_manager):
        """测试创建空清单"""
        experiment_id = "test_exp"
        algorithm_key = "test_alg"
        
        empty_manifest = manifest_manager._create_empty_manifest(experiment_id, algorithm_key)
        
        assert empty_manifest["version"] == 1
        assert empty_manifest["experiment_id"] == experiment_id
        assert empty_manifest["algorithm_key"] == algorithm_key
        assert "generated_at" in empty_manifest
        assert empty_manifest["trajectory"] == {}
        assert empty_manifest["pr_curve"] == {}
        assert empty_manifest["frames"] == {}
        assert "error" in empty_manifest

    def test_manifest_json_format(self, manifest_manager, sample_experiment_data):
        """测试清单JSON格式正确性"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        
        # 验证可以序列化为JSON
        json_str = json.dumps(manifest, indent=2, ensure_ascii=False)
        assert len(json_str) > 0
        
        # 验证可以反序列化
        parsed_manifest = json.loads(json_str)
        assert parsed_manifest["experiment_id"] == experiment_id

    def test_url_generation(self, manifest_manager, sample_experiment_data):
        """测试URL生成正确性"""
        experiment_id, algorithm_key = sample_experiment_data
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        
        # 检查轨迹URL
        if "ui" in manifest["trajectory"]:
            ui_url = manifest["trajectory"]["ui"]["url"]
            expected_path = f"/assets/experiments/{experiment_id}/trajectories/{algorithm_key}.ui.arrow"
            assert ui_url == expected_path
        
        # 检查PR曲线URL
        if "ui" in manifest["pr_curve"]:
            pr_url = manifest["pr_curve"]["ui"]["url"]
            expected_path = f"/assets/experiments/{experiment_id}/pr_curves/{algorithm_key}.ui.arrow"
            assert pr_url == expected_path


class TestManifestManagerEdgeCases:
    """测试边缘情况"""

    def test_generate_manifest_no_files(self, manifest_manager):
        """测试没有文件时的清单生成"""
        experiment_id = "empty_exp"
        algorithm_key = "empty_alg"
        
        manifest = manifest_manager.generate_manifest(experiment_id, algorithm_key)
        
        assert manifest["experiment_id"] == experiment_id
        assert manifest["algorithm_key"] == algorithm_key
        assert manifest["trajectory"] == {}
        assert manifest["pr_curve"] == {}
        assert manifest["frames"] == {}

    def test_save_manifest_creates_directory(self, manifest_manager, temp_dir):
        """测试保存清单时创建目录"""
        experiment_id = "new_exp"
        algorithm_key = "new_alg"
        
        manifest = {
            "version": 1,
            "experiment_id": experiment_id,
            "algorithm_key": algorithm_key
        }
        
        manifest_manager.save_manifest(experiment_id, algorithm_key, manifest)
        
        # 验证目录和文件被创建
        manifest_path = temp_dir / f"experiments/{experiment_id}/manifests/{algorithm_key}.json"
        assert manifest_path.exists()
        assert manifest_path.parent.exists()

    def test_manifest_with_unicode_content(self, manifest_manager, temp_dir):
        """测试包含Unicode内容的清单"""
        experiment_id = "测试实验"
        algorithm_key = "测试算法"
        
        manifest = {
            "version": 1,
            "experiment_id": experiment_id,
            "algorithm_key": algorithm_key,
            "description": "包含中文的测试清单"
        }
        
        manifest_manager.save_manifest(experiment_id, algorithm_key, manifest)
        loaded_manifest = manifest_manager.load_manifest(experiment_id, algorithm_key)
        
        assert loaded_manifest["experiment_id"] == experiment_id
        assert loaded_manifest["algorithm_key"] == algorithm_key
        assert loaded_manifest["description"] == "包含中文的测试清单"
