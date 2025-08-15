#
# 功能: Apache Arrow 列式数据写入器
#
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
    ARROW_AVAILABLE = True
except ImportError:
    logger.warning("PyArrow not available, Arrow writer disabled")
    ARROW_AVAILABLE = False


class ArrowWriter:
    """Apache Arrow 列式数据写入器
    
    用于将轨迹、PR曲线等数据以高效的列式格式存储
    """
    
    def __init__(self, enable_compression: bool = True):
        self.enable_compression = enable_compression
        if not ARROW_AVAILABLE:
            raise ImportError("PyArrow is required for ArrowWriter")
    
    def write_trajectory(
        self, 
        path: Union[str, Path], 
        estimated_trajectory: List[Dict[str, Any]],
        groundtruth_trajectory: Optional[List[Dict[str, Any]]] = None,
        reference_trajectory: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """写入轨迹数据到Arrow格式
        
        Args:
            path: 输出文件路径
            estimated_trajectory: 估计轨迹点列表
            groundtruth_trajectory: 真值轨迹点列表（可选）
            reference_trajectory: 参考轨迹点列表（可选）
            metadata: 元数据（可选）
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建列数据
            columns = {}
            
            # 估计轨迹（必需）
            if estimated_trajectory:
                columns.update(self._extract_trajectory_columns(estimated_trajectory, prefix=""))
            
            # 真值轨迹（可选）
            if groundtruth_trajectory:
                gt_cols = self._extract_trajectory_columns(groundtruth_trajectory, prefix="gt_")
                columns.update(gt_cols)
            
            # 参考轨迹（可选）
            if reference_trajectory:
                ref_cols = self._extract_trajectory_columns(reference_trajectory, prefix="ref_")
                columns.update(ref_cols)
            
            # 创建Arrow表
            arrays = {}
            for col_name, values in columns.items():
                if col_name in ['frame_id']:
                    arrays[col_name] = pa.array(values, type=pa.uint32())
                elif col_name.endswith('_t') or col_name == 't':
                    arrays[col_name] = pa.array(values, type=pa.float64())
                else:
                    arrays[col_name] = pa.array(values, type=pa.float32())
            
            table = pa.Table.from_pydict(arrays)
            
            # 添加元数据到schema
            if metadata:
                schema_metadata = {k: str(v) for k, v in metadata.items()}
                table = table.replace_schema_metadata(schema_metadata)
            
            # 写入文件
            compression = 'zstd' if self.enable_compression else None
            with ipc.new_file(path, table.schema) as sink:
                sink.write(table)
            
            logger.info(f"Arrow轨迹数据已写入: {path} ({len(estimated_trajectory)} 点)")
            
        except Exception as e:
            logger.error(f"写入Arrow轨迹数据失败: {e}")
            raise
    
    def write_pr_curve(
        self,
        path: Union[str, Path],
        precisions: List[float],
        recalls: List[float],
        thresholds: List[float],
        f1_scores: Optional[List[float]] = None,
        raw_precisions: Optional[List[float]] = None,
        raw_recalls: Optional[List[float]] = None,
        raw_thresholds: Optional[List[float]] = None,
        raw_f1_scores: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """写入PR曲线数据到Arrow格式
        
        Args:
            path: 输出文件路径
            precisions: 精度值列表
            recalls: 召回率值列表
            thresholds: 阈值列表
            f1_scores: F1分数列表（可选）
            raw_*: 原始数据（可选，用于UI切换）
            metadata: 元数据（可选）
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建列数据
            columns = {
                'precision': precisions,
                'recall': recalls,
                'threshold': thresholds,
            }
            
            if f1_scores:
                columns['f1'] = f1_scores
            
            # 原始数据（如果提供）
            if raw_precisions:
                columns['raw_precision'] = raw_precisions
            if raw_recalls:
                columns['raw_recall'] = raw_recalls
            if raw_thresholds:
                columns['raw_threshold'] = raw_thresholds
            if raw_f1_scores:
                columns['raw_f1'] = raw_f1_scores
            
            # 创建Arrow表
            arrays = {}
            for col_name, values in columns.items():
                arrays[col_name] = pa.array(values, type=pa.float32())
            
            table = pa.Table.from_pydict(arrays)
            
            # 添加元数据
            if metadata:
                schema_metadata = {k: str(v) for k, v in metadata.items()}
                table = table.replace_schema_metadata(schema_metadata)
            
            # 写入文件
            compression = 'zstd' if self.enable_compression else None
            with ipc.new_file(path, table.schema) as sink:
                sink.write(table)
            
            logger.info(f"Arrow PR曲线数据已写入: {path} ({len(precisions)} 点)")
            
        except Exception as e:
            logger.error(f"写入Arrow PR曲线数据失败: {e}")
            raise
    
    def _extract_trajectory_columns(
        self, 
        trajectory: List[Dict[str, Any]], 
        prefix: str = ""
    ) -> Dict[str, List[float]]:
        """从轨迹点列表提取列数据"""
        columns = {
            f"{prefix}x": [],
            f"{prefix}y": [],
            f"{prefix}z": [],
            f"{prefix}t": [],
        }
        
        # 如果没有前缀，添加frame_id
        if not prefix:
            columns["frame_id"] = []
        
        for point in trajectory:
            columns[f"{prefix}x"].append(float(point.get('x', 0.0)))
            columns[f"{prefix}y"].append(float(point.get('y', 0.0)))
            columns[f"{prefix}z"].append(float(point.get('z', 0.0)))
            columns[f"{prefix}t"].append(float(point.get('timestamp', 0.0)))
            
            if not prefix:
                columns["frame_id"].append(int(point.get('frame_id', 0)))
        
        return columns
    
    def downsample_trajectory(
        self, 
        trajectory: List[Dict[str, Any]], 
        max_points: int
    ) -> List[Dict[str, Any]]:
        """等距下采样轨迹数据"""
        if len(trajectory) <= max_points:
            return trajectory
        
        # 等距采样索引
        indices = np.linspace(0, len(trajectory) - 1, max_points, dtype=int)
        return [trajectory[i] for i in indices]
    
    def downsample_pr_curve(
        self,
        precisions: List[float],
        recalls: List[float],
        thresholds: List[float],
        f1_scores: Optional[List[float]],
        max_points: int
    ) -> tuple:
        """等距下采样PR曲线数据"""
        if len(precisions) <= max_points:
            return precisions, recalls, thresholds, f1_scores
        
        # 等距采样索引
        indices = np.linspace(0, len(precisions) - 1, max_points, dtype=int)
        
        sampled_precisions = [precisions[i] for i in indices]
        sampled_recalls = [recalls[i] for i in indices]
        sampled_thresholds = [thresholds[i] for i in indices]
        sampled_f1_scores = [f1_scores[i] for i in indices] if f1_scores else None
        
        return sampled_precisions, sampled_recalls, sampled_thresholds, sampled_f1_scores


class ArrowReader:
    """Apache Arrow 列式数据读取器"""
    
    def __init__(self):
        if not ARROW_AVAILABLE:
            raise ImportError("PyArrow is required for ArrowReader")
    
    def read_trajectory(self, path: Union[str, Path]) -> Dict[str, Any]:
        """读取Arrow格式的轨迹数据"""
        try:
            path = Path(path)
            if not path.exists():
                return None
            
            with ipc.open_file(path) as source:
                table = source.read_all()
            
            # 提取列数据
            result = {
                "estimated_trajectory": [],
                "groundtruth_trajectory": [],
                "reference_trajectory": [],
                "metadata": dict(table.schema.metadata) if table.schema.metadata else {}
            }
            
            # 估计轨迹
            if all(col in table.column_names for col in ['x', 'y', 'z', 't']):
                x_vals = table.column('x').to_pylist()
                y_vals = table.column('y').to_pylist()
                z_vals = table.column('z').to_pylist()
                t_vals = table.column('t').to_pylist()
                frame_ids = table.column('frame_id').to_pylist() if 'frame_id' in table.column_names else range(len(x_vals))
                
                result["estimated_trajectory"] = [
                    {"x": x, "y": y, "z": z, "timestamp": t, "frame_id": fid}
                    for x, y, z, t, fid in zip(x_vals, y_vals, z_vals, t_vals, frame_ids)
                ]
            
            # 真值轨迹
            if all(col in table.column_names for col in ['gt_x', 'gt_y', 'gt_z', 'gt_t']):
                gt_x = table.column('gt_x').to_pylist()
                gt_y = table.column('gt_y').to_pylist()
                gt_z = table.column('gt_z').to_pylist()
                gt_t = table.column('gt_t').to_pylist()
                
                result["groundtruth_trajectory"] = [
                    {"x": x, "y": y, "z": z, "timestamp": t}
                    for x, y, z, t in zip(gt_x, gt_y, gt_z, gt_t)
                ]
            
            # 参考轨迹
            if all(col in table.column_names for col in ['ref_x', 'ref_y', 'ref_z', 'ref_t']):
                ref_x = table.column('ref_x').to_pylist()
                ref_y = table.column('ref_y').to_pylist()
                ref_z = table.column('ref_z').to_pylist()
                ref_t = table.column('ref_t').to_pylist()
                
                result["reference_trajectory"] = [
                    {"x": x, "y": y, "z": z, "timestamp": t}
                    for x, y, z, t in zip(ref_x, ref_y, ref_z, ref_t)
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"读取Arrow轨迹数据失败: {e}")
            return None
    
    def read_pr_curve(self, path: Union[str, Path]) -> Dict[str, Any]:
        """读取Arrow格式的PR曲线数据"""
        try:
            path = Path(path)
            if not path.exists():
                return None
            
            with ipc.open_file(path) as source:
                table = source.read_all()
            
            result = {
                "precisions": table.column('precision').to_pylist(),
                "recalls": table.column('recall').to_pylist(),
                "thresholds": table.column('threshold').to_pylist(),
                "metadata": dict(table.schema.metadata) if table.schema.metadata else {}
            }
            
            # 可选列
            if 'f1' in table.column_names:
                result["f1_scores"] = table.column('f1').to_pylist()
            
            if 'raw_precision' in table.column_names:
                result["raw_precisions"] = table.column('raw_precision').to_pylist()
                result["raw_recalls"] = table.column('raw_recall').to_pylist()
                result["raw_thresholds"] = table.column('raw_threshold').to_pylist()
                if 'raw_f1' in table.column_names:
                    result["raw_f1_scores"] = table.column('raw_f1').to_pylist()
            
            return result
            
        except Exception as e:
            logger.error(f"读取Arrow PR曲线数据失败: {e}")
            return None
