"""
动态配置管理器

基于Context7最佳实践，实现动态算法发现和配置管理，
避免硬编码算法列表和参数。
"""

import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import cv2

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmCapability:
    """算法能力描述"""
    name: str
    display_name: str
    description: str
    is_available: bool
    requirements: List[str] = field(default_factory=list)
    default_config: Dict[str, Any] = field(default_factory=dict)
    supported_matchers: List[str] = field(default_factory=list)


class DynamicConfigManager:
    """动态配置管理器 - 基于Superposition最佳实践"""
    
    def __init__(self):
        self._feature_capabilities: Dict[str, AlgorithmCapability] = {}
        self._ransac_capabilities: Dict[str, AlgorithmCapability] = {}
        self._chart_config: Dict[str, Any] = {}
        self._discover_algorithms()
        self._load_chart_config()
    
    def _discover_algorithms(self):
        """动态发现所有可用的算法"""
        self._discover_feature_extractors()
        self._discover_ransac_algorithms()
    
    def _discover_feature_extractors(self):
        """发现特征提取器"""
        from src.models.types import FeatureType
        
        # 基础特征提取器映射
        base_extractors = {
            FeatureType.SIFT: {
                "display_name": "SIFT",
                "description": "尺度不变特征变换，适用于高质量图像",
                "requirements": ["opencv-python"],
                "supported_matchers": ["flann", "bf"]
            },
            FeatureType.ORB: {
                "display_name": "ORB",
                "description": "快速二进制特征，适用于实时应用",
                "requirements": ["opencv-python"],
                "supported_matchers": ["bf", "flann"]
            },
            FeatureType.AKAZE: {
                "display_name": "AKAZE",
                "description": "加速KAZE特征，平衡速度和质量",
                "requirements": ["opencv-python"],
                "supported_matchers": ["bf", "flann"]
            },
            FeatureType.BRISK: {
                "display_name": "BRISK",
                "description": "二进制鲁棒不变特征",
                "requirements": ["opencv-python"],
                "supported_matchers": ["bf"]
            },
            FeatureType.KAZE: {
                "display_name": "KAZE",
                "description": "非线性尺度空间特征",
                "requirements": ["opencv-python"],
                "supported_matchers": ["flann", "bf"]
            },
            FeatureType.SURF: {
                "display_name": "SURF",
                "description": "加速鲁棒特征（需要额外依赖）",
                "requirements": ["opencv-contrib-python"],
                "supported_matchers": ["flann", "bf"]
            }
        }
        
        for feature_type, info in base_extractors.items():
            is_available = self._check_feature_availability(feature_type)
            
            self._feature_capabilities[feature_type.value] = AlgorithmCapability(
                name=feature_type.value,
                display_name=info["display_name"],
                description=info["description"],
                is_available=is_available,
                requirements=info["requirements"],
                default_config=self._get_default_feature_config(feature_type),
                supported_matchers=info["supported_matchers"]
            )
    
    def _discover_ransac_algorithms(self):
        """发现RANSAC算法"""
        ransac_algorithms = {
            "STANDARD": {
                "display_name": "标准RANSAC",
                "description": "经典RANSAC算法",
                "opencv_constant": cv2.RANSAC
            },
            "PROSAC": {
                "display_name": "PROSAC",
                "description": "渐进式采样一致性算法",
                "opencv_constant": getattr(cv2, 'USAC_PROSAC', cv2.RANSAC)
            },
            "USAC_DEFAULT": {
                "display_name": "USAC默认",
                "description": "通用采样一致性算法",
                "opencv_constant": getattr(cv2, 'USAC_DEFAULT', cv2.RANSAC)
            },
            "USAC_MAGSAC": {
                "display_name": "MAGSAC",
                "description": "边际化采样一致性算法",
                "opencv_constant": getattr(cv2, 'USAC_MAGSAC', cv2.RANSAC)
            },
            "USAC_ACCURATE": {
                "display_name": "USAC精确",
                "description": "高精度USAC算法",
                "opencv_constant": getattr(cv2, 'USAC_ACCURATE', cv2.RANSAC)
            },
            "RHO": {
                "display_name": "RHO",
                "description": "快速鲁棒估计算法",
                "opencv_constant": getattr(cv2, 'RHO', cv2.RANSAC)
            },
            "LMEDS": {
                "display_name": "LMedS",
                "description": "最小中位数平方算法",
                "opencv_constant": cv2.LMEDS
            }
        }
        
        for name, info in ransac_algorithms.items():
            is_available = hasattr(cv2, info["opencv_constant"]) if isinstance(info["opencv_constant"], str) else True
            
            self._ransac_capabilities[name] = AlgorithmCapability(
                name=name,
                display_name=info["display_name"],
                description=info["description"],
                is_available=is_available,
                requirements=["opencv-python"],
                default_config=self._get_default_ransac_config(name)
            )
    
    def _check_feature_availability(self, feature_type) -> bool:
        """检查特征提取器是否可用"""
        try:
            if feature_type.value == "SURF":
                # SURF需要opencv-contrib-python
                import cv2
                cv2.xfeatures2d.SURF_create()
                return True
            else:
                # 其他特征提取器在标准opencv中可用
                return True
        except Exception:
            return False

    def _get_default_feature_config(self, feature_type) -> Dict[str, Any]:
        """获取特征提取器默认配置"""
        # 这里可以从配置文件或环境变量加载
        configs = {
            "SIFT": {
                "extractor": {
                    "nfeatures": 0,
                    "nOctaveLayers": 3,
                    "contrastThreshold": 0.04,
                    "edgeThreshold": 10,
                    "sigma": 1.6,
                },
                "matcher": {"matcher_type": "flann", "ratio_threshold": 0.75}
            },
            "ORB": {
                "extractor": {
                    "nfeatures": 5000,
                    "scaleFactor": 1.2,
                    "nlevels": 8,
                    "edgeThreshold": 31,
                    "firstLevel": 0,
                    "WTA_K": 2,
                    "scoreType": cv2.ORB_HARRIS_SCORE,
                    "patchSize": 31,
                    "fastThreshold": 20,
                },
                "matcher": {
                    "matcher_type": "bf",
                    "normType": cv2.NORM_HAMMING,
                    "crossCheck": True,
                    "ratio_threshold": 0.75,
                }
            }
            # 其他配置...
        }
        return configs.get(feature_type.value, {})
    
    def _get_default_ransac_config(self, ransac_type: str) -> Dict[str, Any]:
        """获取RANSAC算法默认配置"""
        return {
            "threshold": 1.0,
            "confidence": 0.999,
            "max_iters": 2000
        }
    
    def _load_chart_config(self):
        """加载图表配置"""
        self._chart_config = {
            "pr_curve": {
                "max_frames": 1000,
                "max_samples": 3000,
                "cache_ttl": 300
            },
            "trajectory": {
                "max_frames": 500,
                "cache_ttl": 300
            },
            "metrics": {
                "cache_ttl": 300
            }
        }
    
    # 公共接口方法
    def get_available_feature_types(self) -> List[str]:
        """获取可用的特征类型"""
        return [name for name, cap in self._feature_capabilities.items() if cap.is_available]
    
    def get_available_ransac_types(self) -> List[str]:
        """获取可用的RANSAC类型"""
        return [name for name, cap in self._ransac_capabilities.items() if cap.is_available]
    
    def get_feature_capability(self, feature_type: str) -> Optional[AlgorithmCapability]:
        """获取特征算法能力"""
        return self._feature_capabilities.get(feature_type)
    
    def get_ransac_capability(self, ransac_type: str) -> Optional[AlgorithmCapability]:
        """获取RANSAC算法能力"""
        return self._ransac_capabilities.get(ransac_type)
    
    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """获取图表配置"""
        return self._chart_config.get(chart_type, {})
    
    def is_feature_available(self, feature_type: str) -> bool:
        """检查特征类型是否可用"""
        cap = self._feature_capabilities.get(feature_type)
        return cap.is_available if cap else False
    
    def is_ransac_available(self, ransac_type: str) -> bool:
        """检查RANSAC类型是否可用"""
        cap = self._ransac_capabilities.get(ransac_type)
        return cap.is_available if cap else False


# 全局实例
_dynamic_config_manager = None

def get_dynamic_config_manager() -> DynamicConfigManager:
    """获取动态配置管理器实例"""
    global _dynamic_config_manager
    if _dynamic_config_manager is None:
        _dynamic_config_manager = DynamicConfigManager()
    return _dynamic_config_manager
