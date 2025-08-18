# -*- coding: utf-8 -*-
"""
Datasets API

Provides endpoints to list and validate datasets under DATASETS_ROOT.
Enables the frontend DatasetBrowser to discover datasets without hardcoding paths.

Routes:
- GET /api/v1/datasets/           -> list datasets discovered under configured roots
- POST /api/v1/datasets/validate  -> validate a dataset path

The service prefers app.config['DATASETS_ROOT'], but will gracefully fall back to './datasets'.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Any

from flask import Blueprint, current_app, jsonify, request

from src.datasets.factory import DatasetFactory

bp = Blueprint("datasets", __name__, url_prefix="/api/v1/datasets")


def _get_scan_roots() -> List[Path]:
    roots: List[Path] = []
    cfg_root = current_app.config.get("DATASETS_ROOT")
    if cfg_root:
        roots.append(Path(cfg_root))
    # Fallback to ../datasets at repo root (one level up from backend/)
    fallback = Path("../datasets")
    if fallback not in roots:
        roots.append(fallback)
    # Deduplicate and keep existing only
    uniq: List[Path] = []
    seen = set()
    for r in roots:
        rp = r.resolve()
        if str(rp) in seen:
            continue
        seen.add(str(rp))
        uniq.append(rp)
    return uniq


def _detect_dataset_format(d: Path) -> str:
    """使用数据集工厂检测格式"""
    return DatasetFactory.detect_dataset_type(d)


def _to_dataset_entry(d: Path) -> Dict[str, Any]:
    """创建数据集条目，包含实际的帧数信息"""
    fmt = _detect_dataset_format(d)
    has_gt = (d / "groundtruth.txt").exists() or (d / "poses.txt").exists()

    # 使用数据集工厂获取实际信息
    total_frames = 0
    sequences_info = []
    format_valid = True

    try:
        dataset = DatasetFactory.create_dataset(d)
        sequences = dataset.get_sequences()

        for seq in sequences:
            frame_count = dataset.get_frame_count(seq)
            total_frames += frame_count
            sequences_info.append({
                "name": seq,
                "path": str(d.resolve()),
                "frames": frame_count,
            })

        # 验证数据集
        validation = dataset.validate()
        format_valid = validation["valid"]

    except Exception as e:
        # 如果无法加载数据集，使用默认值
        sequences_info = [{
            "name": d.name,
            "path": str(d.resolve()),
            "frames": 0,
        }]
        format_valid = False

    entry = {
        "name": d.name,
        "path": str(d.resolve()),
        "format": fmt,
        "type": fmt,
        "description": None,
        "total_frames": total_frames,
        "sequences": sequences_info,
        "format_valid": format_valid,
        "last_modified": None,
        "has_groundtruth": has_gt,
    }
    return entry


def _discover_datasets(root: Path) -> List[Dict[str, Any]]:
    datasets: List[Dict[str, Any]] = []
    if not root.exists():
        return datasets

    # Strategy: look for leaf directories that look like datasets up to 2 levels deep
    candidates: List[Path] = []
    try:
        for child in root.iterdir():
            if child.is_dir():
                # Direct child could be dataset
                candidates.append(child)
                # Also look one level deeper (e.g., datasets/tum/<dataset_dir>)
                for sub in child.iterdir():
                    if sub.is_dir():
                        candidates.append(sub)
    except Exception:
        pass

    # Filter candidates that contain some known files/dirs or any image folder
    def looks_like_dataset(p: Path) -> bool:
        if any((p / name).exists() for name in ["rgb.txt", "depth.txt", "groundtruth.txt", "mav0", "image_0", "image_1"]):
            return True
        # Generic heuristic: contains at least one subdir with many files (images)
        try:
            for sub in p.iterdir():
                if sub.is_dir():
                    # if directory contains > 10 files, likely a frame folder
                    count = sum(1 for _ in sub.iterdir())
                    if count >= 10:
                        return True
        except Exception:
            return False
        return False

    seen_paths = set()
    for cand in candidates:
        if cand.is_dir() and looks_like_dataset(cand):
            key = str(cand.resolve())
            if key in seen_paths:
                continue
            seen_paths.add(key)
            datasets.append(_to_dataset_entry(cand))

    return datasets


@bp.route("/", methods=["GET"])
def list_datasets():
    roots = _get_scan_roots()
    found: List[Dict[str, Any]] = []
    for r in roots:
        found.extend(_discover_datasets(r))
    # Deduplicate by absolute path
    unique: Dict[str, Dict[str, Any]] = {d["path"]: d for d in found}
    return (
        jsonify(
            {
                "datasets": list(unique.values()),
                "total_count": len(unique),
                "scan_paths": [str(r) for r in roots],
            }
        ),
        200,
    )


@bp.route("/validate", methods=["POST"])
def validate_dataset():
    """验证数据集路径和格式"""
    data = request.get_json(force=True) or {}
    path_str = str(data.get("path", "")).strip()

    if not path_str:
        return jsonify({
            "valid": False,
            "dataset_type": None,
            "issues": ["路径不能为空"],
            "suggestions": ["请提供有效的数据集路径"],
            "statistics": {},
        }), 400

    path = Path(path_str)

    # 使用数据集工厂进行验证
    try:
        result = DatasetFactory.validate_dataset_path(path)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "valid": False,
            "dataset_type": "Unknown",
            "issues": [f"验证失败: {e}"],
            "suggestions": ["请检查数据集路径和格式"],
            "statistics": {},
        }), 200

