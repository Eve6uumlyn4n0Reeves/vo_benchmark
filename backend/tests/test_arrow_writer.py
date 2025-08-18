"""
测试 Arrow 数据写入器和读取器
"""
import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

# 直接导入避免循环依赖
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.storage.arrow_writer import ArrowWriter, ArrowReader, ARROW_AVAILABLE
except ImportError:
    # 如果导入失败，跳过所有测试
    ARROW_AVAILABLE = False
    ArrowWriter = None
    ArrowReader = None


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_trajectory():
    """示例轨迹数据"""
    return [
        {"x": 1.0, "y": 2.0, "z": 3.0, "timestamp": 0.1, "frame_id": 1},
        {"x": 1.1, "y": 2.1, "z": 3.1, "timestamp": 0.2, "frame_id": 2},
        {"x": 1.2, "y": 2.2, "z": 3.2, "timestamp": 0.3, "frame_id": 3},
    ]


@pytest.fixture
def sample_pr_curve():
    """示例PR曲线数据"""
    return {
        "precisions": [0.9, 0.8, 0.7],
        "recalls": [0.1, 0.5, 0.9],
        "thresholds": [0.9, 0.5, 0.1],
        "f1_scores": [0.18, 0.62, 0.78],
    }


@pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
class TestArrowWriter:
    """测试 Arrow 写入器"""

    def test_write_trajectory_basic(self, temp_dir, sample_trajectory):
        """测试基本轨迹写入"""
        writer = ArrowWriter()
        output_path = temp_dir / "trajectory.arrow"
        
        writer.write_trajectory(
            output_path,
            sample_trajectory,
            metadata={"test": "value"}
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_write_trajectory_with_gt_ref(self, temp_dir, sample_trajectory):
        """测试包含真值和参考轨迹的写入"""
        writer = ArrowWriter()
        output_path = temp_dir / "trajectory_full.arrow"
        
        gt_trajectory = [
            {"x": 1.05, "y": 2.05, "z": 3.05, "timestamp": 0.1},
            {"x": 1.15, "y": 2.15, "z": 3.15, "timestamp": 0.2},
        ]
        
        ref_trajectory = [
            {"x": 0.95, "y": 1.95, "z": 2.95, "timestamp": 0.1},
            {"x": 1.05, "y": 2.05, "z": 3.05, "timestamp": 0.2},
        ]
        
        writer.write_trajectory(
            output_path,
            sample_trajectory,
            gt_trajectory,
            ref_trajectory,
            metadata={"version": "full"}
        )
        
        assert output_path.exists()

    def test_write_pr_curve_basic(self, temp_dir, sample_pr_curve):
        """测试基本PR曲线写入"""
        writer = ArrowWriter()
        output_path = temp_dir / "pr_curve.arrow"
        
        writer.write_pr_curve(
            output_path,
            sample_pr_curve["precisions"],
            sample_pr_curve["recalls"],
            sample_pr_curve["thresholds"],
            sample_pr_curve["f1_scores"],
            metadata={"auc_score": "0.85"}
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_write_pr_curve_with_raw(self, temp_dir, sample_pr_curve):
        """测试包含原始数据的PR曲线写入"""
        writer = ArrowWriter()
        output_path = temp_dir / "pr_curve_raw.arrow"
        
        raw_precisions = [0.95, 0.85, 0.75, 0.65]
        raw_recalls = [0.05, 0.25, 0.65, 0.95]
        raw_thresholds = [0.95, 0.75, 0.25, 0.05]
        raw_f1_scores = [0.095, 0.385, 0.695, 0.765]
        
        writer.write_pr_curve(
            output_path,
            sample_pr_curve["precisions"],
            sample_pr_curve["recalls"],
            sample_pr_curve["thresholds"],
            sample_pr_curve["f1_scores"],
            raw_precisions,
            raw_recalls,
            raw_thresholds,
            raw_f1_scores,
            metadata={"version": "full"}
        )
        
        assert output_path.exists()

    def test_downsample_trajectory(self, sample_trajectory):
        """测试轨迹下采样"""
        writer = ArrowWriter()
        
        # 创建更大的轨迹数据
        large_trajectory = []
        for i in range(100):
            large_trajectory.append({
                "x": float(i), "y": float(i*2), "z": float(i*3),
                "timestamp": float(i*0.1), "frame_id": i
            })
        
        # 下采样到10个点
        downsampled = writer.downsample_trajectory(large_trajectory, 10)
        
        assert len(downsampled) == 10
        assert downsampled[0] == large_trajectory[0]  # 第一个点
        assert downsampled[-1] == large_trajectory[-1]  # 最后一个点

    def test_downsample_pr_curve(self, sample_pr_curve):
        """测试PR曲线下采样"""
        writer = ArrowWriter()
        
        # 创建更大的PR曲线数据
        large_precisions = [0.9 - i*0.01 for i in range(50)]
        large_recalls = [i*0.02 for i in range(50)]
        large_thresholds = [0.9 - i*0.018 for i in range(50)]
        large_f1_scores = [2*p*r/(p+r) if p+r > 0 else 0 for p, r in zip(large_precisions, large_recalls)]
        
        # 下采样到10个点
        p, r, t, f = writer.downsample_pr_curve(
            large_precisions, large_recalls, large_thresholds, large_f1_scores, 10
        )
        
        assert len(p) == 10
        assert len(r) == 10
        assert len(t) == 10
        assert len(f) == 10


@pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
class TestArrowReader:
    """测试 Arrow 读取器"""

    def test_read_trajectory_basic(self, temp_dir, sample_trajectory):
        """测试基本轨迹读取"""
        # 先写入数据
        writer = ArrowWriter()
        output_path = temp_dir / "trajectory.arrow"
        writer.write_trajectory(
            output_path,
            sample_trajectory,
            metadata={"test": "value"}
        )
        
        # 读取数据
        reader = ArrowReader()
        result = reader.read_trajectory(output_path)
        
        assert result is not None
        assert "estimated_trajectory" in result
        assert len(result["estimated_trajectory"]) == len(sample_trajectory)
        
        # 验证数据内容
        for i, point in enumerate(result["estimated_trajectory"]):
            assert abs(point["x"] - sample_trajectory[i]["x"]) < 1e-6
            assert abs(point["y"] - sample_trajectory[i]["y"]) < 1e-6
            assert abs(point["z"] - sample_trajectory[i]["z"]) < 1e-6
            assert abs(point["timestamp"] - sample_trajectory[i]["timestamp"]) < 1e-9
            assert point["frame_id"] == sample_trajectory[i]["frame_id"]

    def test_read_trajectory_with_gt_ref(self, temp_dir, sample_trajectory):
        """测试读取包含真值和参考轨迹的数据"""
        gt_trajectory = [
            {"x": 1.05, "y": 2.05, "z": 3.05, "timestamp": 0.1},
            {"x": 1.15, "y": 2.15, "z": 3.15, "timestamp": 0.2},
        ]
        
        ref_trajectory = [
            {"x": 0.95, "y": 1.95, "z": 2.95, "timestamp": 0.1},
            {"x": 1.05, "y": 2.05, "z": 3.05, "timestamp": 0.2},
        ]
        
        # 写入数据
        writer = ArrowWriter()
        output_path = temp_dir / "trajectory_full.arrow"
        writer.write_trajectory(
            output_path,
            sample_trajectory,
            gt_trajectory,
            ref_trajectory
        )
        
        # 读取数据
        reader = ArrowReader()
        result = reader.read_trajectory(output_path)
        
        assert result is not None
        assert len(result["estimated_trajectory"]) == len(sample_trajectory)
        # gt/ref 可被填充为与 estimated 等长（尾部 NaN），因此这里只断言至少包含原有点数
        assert len(result["groundtruth_trajectory"]) >= len(gt_trajectory)
        assert len(result["reference_trajectory"]) >= len(ref_trajectory)

    def test_read_pr_curve_basic(self, temp_dir, sample_pr_curve):
        """测试基本PR曲线读取"""
        # 写入数据
        writer = ArrowWriter()
        output_path = temp_dir / "pr_curve.arrow"
        writer.write_pr_curve(
            output_path,
            sample_pr_curve["precisions"],
            sample_pr_curve["recalls"],
            sample_pr_curve["thresholds"],
            sample_pr_curve["f1_scores"],
            metadata={"auc_score": "0.85"}
        )
        
        # 读取数据
        reader = ArrowReader()
        result = reader.read_pr_curve(output_path)
        
        assert result is not None
        assert "precisions" in result
        assert "recalls" in result
        assert "thresholds" in result
        assert "f1_scores" in result
        assert "metadata" in result
        
        # 验证数据内容
        for a, b in zip(result["precisions"], sample_pr_curve["precisions"]):
            assert abs(a - b) < 1e-6
        for a, b in zip(result["recalls"], sample_pr_curve["recalls"]):
            assert abs(a - b) < 1e-6
        for a, b in zip(result["thresholds"], sample_pr_curve["thresholds"]):
            assert abs(a - b) < 1e-6
        for a, b in zip(result["f1_scores"], sample_pr_curve["f1_scores"]):
            assert abs(a - b) < 1e-6
        assert result["metadata"]["auc_score"] == "0.85"

    def test_read_nonexistent_file(self, temp_dir):
        """测试读取不存在的文件"""
        reader = ArrowReader()
        result = reader.read_trajectory(temp_dir / "nonexistent.arrow")
        assert result is None
        
        result = reader.read_pr_curve(temp_dir / "nonexistent.arrow")
        assert result is None


@pytest.mark.skipif(ARROW_AVAILABLE, reason="Test for when PyArrow is not available")
class TestArrowUnavailable:
    """测试 PyArrow 不可用时的行为"""

    def test_arrow_writer_import_error(self):
        """测试 ArrowWriter 在 PyArrow 不可用时抛出错误"""
        with pytest.raises(ImportError):
            ArrowWriter()

    def test_arrow_reader_import_error(self):
        """测试 ArrowReader 在 PyArrow 不可用时抛出错误"""
        with pytest.raises(ImportError):
            ArrowReader()


class TestArrowIntegration:
    """集成测试"""

    @pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
    def test_write_read_roundtrip(self, temp_dir, sample_trajectory, sample_pr_curve):
        """测试写入-读取往返"""
        writer = ArrowWriter()
        reader = ArrowReader()
        
        # 轨迹数据往返
        traj_path = temp_dir / "trajectory.arrow"
        writer.write_trajectory(traj_path, sample_trajectory)
        traj_result = reader.read_trajectory(traj_path)
        
        assert len(traj_result["estimated_trajectory"]) == len(sample_trajectory)
        
        # PR曲线数据往返
        pr_path = temp_dir / "pr_curve.arrow"
        writer.write_pr_curve(
            pr_path,
            sample_pr_curve["precisions"],
            sample_pr_curve["recalls"],
            sample_pr_curve["thresholds"],
            sample_pr_curve["f1_scores"]
        )
        pr_result = reader.read_pr_curve(pr_path)
        
        assert pr_result["precisions"] == sample_pr_curve["precisions"]
        assert pr_result["recalls"] == sample_pr_curve["recalls"]
