import os
from pathlib import Path
import pytest

from src.datasets.tum import TUMDataset
from src.datasets.kitti import KITTIDataset


def test_tum_get_timestamp_and_fps(tmp_path: Path):
    # 准备一个最小可用的 TUM 目录结构: seq/rgb/ 两张图
    seq_dir = tmp_path / "fr3" / "seqA"
    rgb_dir = seq_dir / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)

    # 以文件名作为时间戳
    (rgb_dir / "1.000000.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (rgb_dir / "1.033333.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    ds = TUMDataset(path=tmp_path / "fr3", config={})

    seq_name = "seqA"
    assert seq_name in ds.get_sequences()

    # 基于文件名可得到非零时间戳
    t0 = ds.get_timestamp(seq_name, 0)
    t1 = ds.get_timestamp(seq_name, 1)
    assert t0 >= 0.0
    assert t1 > t0

    # fps 可由相邻时间戳推断为约 30（这里是 1/0.0333≈30）
    fps = ds.get_fps(seq_name)
    assert fps > 0


def test_kitti_get_timestamp_and_fps(tmp_path: Path):
    # 准备 KITTI 最小结构: sequences/00/image_0 两张图
    seq_dir = tmp_path / "sequences" / "00" / "image_0"
    seq_dir.mkdir(parents=True, exist_ok=True)

    # 仅需存在文件即可初始化（内容不读取）
    (seq_dir / "000000.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (seq_dir / "000001.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    ds = KITTIDataset(path=tmp_path, config={})

    seq_name = "00"
    assert seq_name in ds.get_sequences()

    # 时间戳按 10Hz 近似
    assert ds.get_timestamp(seq_name, 0) == 0.0
    assert ds.get_timestamp(seq_name, 1) == pytest.approx(0.1, rel=1e-6)

    # fps=10
    assert ds.get_fps(seq_name) == 10.0

