import math
from pathlib import Path
import pytest

# Detect pyarrow availability for conditional skipping
try:
    import pyarrow  # noqa: F401
    ARROW_AVAILABLE = True
except Exception:  # pragma: no cover
    ARROW_AVAILABLE = False

# 为避免导入触发其他模块加载导致循环引用，这里使用按路径动态加载
import importlib.util
from pathlib import Path as _Path

def _load_rw():
    storage_mod = _Path(__file__).parents[1] / "src" / "storage" / "arrow_writer.py"
    spec = importlib.util.spec_from_file_location("arrow_writer_for_test", str(storage_mod))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod.ArrowWriter, mod.ArrowReader


@pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
class TestArrowPaddingBehavior:
    def test_trajectory_gt_ref_padding(self, tmp_path: Path):
        ArrowWriter, ArrowReader = _load_rw()
        writer = ArrowWriter()
        reader = ArrowReader()
        out = tmp_path / "traj.arrow"

        # estimated: 3 points
        est = [
            {"x": 1.0, "y": 2.0, "z": 3.0, "timestamp": 0.1, "frame_id": 1},
            {"x": 1.1, "y": 2.1, "z": 3.1, "timestamp": 0.2, "frame_id": 2},
            {"x": 1.2, "y": 2.2, "z": 3.2, "timestamp": 0.3, "frame_id": 3},
        ]
        # gt: only 2 points (will be padded to 3)
        gt = [
            {"x": 1.05, "y": 2.05, "z": 3.05, "timestamp": 0.1},
            {"x": 1.15, "y": 2.15, "z": 3.15, "timestamp": 0.2},
        ]
        # ref: only 1 point (will be padded to 3)
        ref = [
            {"x": 0.95, "y": 1.95, "z": 2.95, "timestamp": 0.1},
        ]

        writer.write_trajectory(out, est, gt, ref)
        data = reader.read_trajectory(out)
        assert data is not None

        est_len = len(est)
        assert len(data["estimated_trajectory"]) == est_len
        assert len(data["groundtruth_trajectory"]) == est_len
        assert len(data["reference_trajectory"]) == est_len

        # Last gt/ref entries are padded with NaN
        last_gt = data["groundtruth_trajectory"][-1]
        last_ref = data["reference_trajectory"][-1]
        assert math.isnan(last_gt["x"]) and math.isnan(last_gt["y"]) and math.isnan(last_gt["z"]) and math.isnan(last_gt["timestamp"])  # type: ignore[index]
        assert math.isnan(last_ref["x"]) and math.isnan(last_ref["y"]) and math.isnan(last_ref["z"]) and math.isnan(last_ref["timestamp"])  # type: ignore[index]

    def test_pr_curve_raw_padding_and_truncation(self, tmp_path: Path):
        ArrowWriter, ArrowReader = _load_rw()
        writer = ArrowWriter()
        reader = ArrowReader()
        out = tmp_path / "pr.arrow"

        precisions = [0.9, 0.8, 0.7]
        recalls = [0.1, 0.5, 0.9]
        thresholds = [0.9, 0.5, 0.1]
        f1 = [0.18, 0.62, 0.78]

        raw_precisions = [0.95, 0.85, 0.75, 0.65]  # longer -> should be truncated to 3
        raw_recalls = [0.05, 0.25]  # shorter -> should be padded to 3
        raw_thresholds = None
        raw_f1 = [0.095, 0.385, 0.695, 0.765]  # longer -> should be truncated to 3

        writer.write_pr_curve(
            out,
            precisions,
            recalls,
            thresholds,
            f1,
            raw_precisions,
            raw_recalls,
            raw_thresholds,
            raw_f1,
            metadata={"version": "test"},
        )

        pr = reader.read_pr_curve(out)
        assert pr is not None

        # Lengths align to base (3)
        assert len(pr["precisions"]) == 3
        assert len(pr["recalls"]) == 3
        assert len(pr["thresholds"]) == 3

        assert len(pr["raw_precisions"]) == 3
        assert len(pr["raw_recalls"]) == 3
        # raw_thresholds omitted -> key may not exist
        assert len(pr.get("raw_f1_scores", [])) in (0, 3)

        # Truncation check (float rounding differences allowed)
        for a, b in zip(pr["raw_precisions"][0:3], raw_precisions[0:3]):
            assert abs(a - b) < 1e-6
        # Padding check (last is NaN)
        assert math.isnan(pr["raw_recalls"][2])

