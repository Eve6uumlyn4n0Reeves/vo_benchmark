#
# 功能: 创建特征提取和匹配相关类的工厂。
#
from typing import Dict, Any, List
import cv2
import logging
from src.models.types import FeatureType
from src.core.features.base import FeatureExtractor
from src.core.features.sift import SIFTExtractor
from src.core.features.orb import ORBExtractor
from src.core.features.akaze import AKAZEExtractor
from src.core.features.brisk import BRISKExtractor
from src.core.features.kaze import KAZEExtractor
# 注意：SURF 仅在安装 opencv-contrib-python 时可用，避免在模块导入时失败，改为按需延迟导入
from src.core.features.matcher import FeatureMatcher, BruteForceMatcher, FLANNMatcher

logger = logging.getLogger(__name__)


class FeatureFactory:
    """特征提取和匹配器工厂类"""

    @staticmethod
    def create_extractor(
        feature_type: FeatureType, config: Dict[str, Any]
    ) -> FeatureExtractor:
        """
        根据特征类型创建特征提取器实例

        Args:
            feature_type: 特征类型 (SIFT/ORB)
            config: 提取器配置参数

        Returns:
            FeatureExtractor: 特征提取器实例

        Raises:
            ValueError: 不支持的特征类型
        """
        try:
            if feature_type == FeatureType.SIFT:
                logger.info(f"创建SIFT特征提取器，配置: {config}")
                return SIFTExtractor(config)
            elif feature_type == FeatureType.ORB:
                logger.info(f"创建ORB特征提取器，配置: {config}")
                return ORBExtractor(config)
            elif feature_type == FeatureType.AKAZE:
                logger.info(f"创建AKAZE特征提取器，配置: {config}")
                return AKAZEExtractor(config)
            elif feature_type == FeatureType.BRISK:
                logger.info(f"创建BRISK特征提取器，配置: {config}")
                return BRISKExtractor(config)
            elif feature_type == FeatureType.KAZE:
                logger.info(f"创建KAZE特征提取器，配置: {config}")
                return KAZEExtractor(config)
            elif feature_type == FeatureType.SURF:
                logger.info(f"创建SURF特征提取器（研究用途），配置: {config}")
                try:
                    from src.core.features.surf import SURFExtractor  # 延迟导入
                except Exception as e:
                    logger.warning("SURF 不可用（可能缺少 opencv-contrib-python）：%s", e)
                    raise ValueError("SURF 不可用：请安装 opencv-contrib-python 或禁用该算法")
                return SURFExtractor(config)
            else:
                raise ValueError(f"不支持的特征类型: {feature_type}")
        except Exception as e:
            logger.error(f"创建特征提取器失败: {e}")
            raise

    @staticmethod
    def create_matcher(
        feature_type: FeatureType, config: Dict[str, Any]
    ) -> FeatureMatcher:
        """
        根据特征类型创建合适的匹配器实例

        Args:
            feature_type: 特征类型 (SIFT/ORB)
            config: 匹配器配置参数

        Returns:
            FeatureMatcher: 特征匹配器实例

        Raises:
            ValueError: 不支持的特征类型
        """
        try:
            # 根据特征类型选择默认匹配器类型和参数
            matcher_type = config.get("matcher_type", "auto")

            if matcher_type == "auto":
                # 自动选择匹配器类型
                if feature_type == FeatureType.SIFT:
                    matcher_type = "flann"
                    # SIFT使用FLANN + KDTREE
                    default_config = {
                        "algorithm": "kdtree",
                        "index_params": {"algorithm": 1, "trees": 5},
                        "search_params": {"checks": 50},
                        "ratio_threshold": 0.75,
                    }
                elif feature_type in (FeatureType.ORB, FeatureType.BRISK, FeatureType.AKAZE):
                    matcher_type = "flann" if feature_type == FeatureType.AKAZE and config.get("use_flann_lsh", True) else "bf"
                    # 二值描述子默认 Hamming；AKAZE-MLDB 可用 FLANN-LSH
                    if matcher_type == "flann":
                        default_config = {
                            "algorithm": "lsh",
                            "index_params": {
                                "algorithm": 6,
                                "table_number": 6,
                                "key_size": 12,
                                "multi_probe_level": 1,
                            },
                            "search_params": {"checks": 50},
                            "ratio_threshold": 0.75,
                        }
                    else:
                        default_config = {
                            "normType": cv2.NORM_HAMMING,
                            "crossCheck": True,
                            "ratio_threshold": 0.75,
                        }
                elif feature_type in (FeatureType.KAZE, FeatureType.SURF):
                    matcher_type = "flann"
                    default_config = {
                        "algorithm": "kdtree",
                        "index_params": {"algorithm": 1, "trees": 5},
                        "search_params": {"checks": 50},
                        "ratio_threshold": 0.75,
                    }
                else:
                    raise ValueError(f"不支持的特征类型: {feature_type}")
            else:
                # 使用指定的匹配器类型
                if feature_type == FeatureType.SIFT:
                    default_config = {"normType": cv2.NORM_L2, "ratio_threshold": 0.75}
                else:
                    default_config = {
                        "normType": cv2.NORM_HAMMING,
                        "ratio_threshold": 0.75,
                    }

            # 合并配置
            final_config = {**default_config, **config}

            # 创建匹配器
            if matcher_type in ["bf", "brute_force"]:
                logger.info(
                    f"创建暴力匹配器，特征类型: {feature_type}, 配置: {final_config}"
                )
                return BruteForceMatcher(final_config)
            elif matcher_type == "flann":
                logger.info(
                    f"创建FLANN匹配器，特征类型: {feature_type}, 配置: {final_config}"
                )
                return FLANNMatcher(final_config)
            else:
                raise ValueError(f"不支持的匹配器类型: {matcher_type}")

        except Exception as e:
            logger.error(f"创建特征匹配器失败: {e}")
            raise

    @staticmethod
    def get_supported_feature_types() -> List[str]:
        """返回支持的特征类型列表"""
        return [t.value for t in FeatureType]

    @staticmethod
    def get_supported_matcher_types() -> List[str]:
        """返回支持的匹配器类型列表"""
        return ["auto", "bf", "brute_force", "flann"]

    @staticmethod
    def get_default_config(feature_type: FeatureType) -> Dict[str, Any]:
        """
        获取指定特征类型的默认配置

        Args:
            feature_type: 特征类型

        Returns:
            Dict[str, Any]: 默认配置参数
        """
        if feature_type == FeatureType.SIFT:
            return {
                "extractor": {
                    "nfeatures": 0,
                    "nOctaveLayers": 3,
                    "contrastThreshold": 0.04,
                    "edgeThreshold": 10,
                    "sigma": 1.6,
                },
                "matcher": {"matcher_type": "flann", "ratio_threshold": 0.75},
            }
        elif feature_type == FeatureType.ORB:
            return {
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
                },
            }
        elif feature_type == FeatureType.AKAZE:
            return {
                "extractor": {
                    "descriptor_type": cv2.AKAZE_DESCRIPTOR_MLDB,
                    "descriptor_size": 0,
                    "descriptor_channels": 3,
                    "threshold": 0.001,
                    "nOctaves": 4,
                    "nOctaveLayers": 4,
                },
                "matcher": {
                    "matcher_type": "flann",
                    "algorithm": "lsh",
                    "index_params": {"algorithm": 6, "table_number": 6, "key_size": 12, "multi_probe_level": 1},
                    "search_params": {"checks": 50},
                    "ratio_threshold": 0.75,
                },
            }
        elif feature_type == FeatureType.BRISK:
            return {
                "extractor": {"thresh": 30, "octaves": 3, "patternScale": 1.0},
                "matcher": {
                    "matcher_type": "bf",
                    "normType": cv2.NORM_HAMMING,
                    "crossCheck": True,
                    "ratio_threshold": 0.75,
                },
            }
        elif feature_type == FeatureType.KAZE:
            return {
                "extractor": {
                    "extended": False,
                    "upright": False,
                    "threshold": 0.001,
                    "nOctaves": 4,
                    "nOctaveLayers": 4,
                },
                "matcher": {
                    "matcher_type": "flann",
                    "algorithm": "kdtree",
                    "index_params": {"algorithm": 1, "trees": 5},
                    "search_params": {"checks": 50},
                    "ratio_threshold": 0.75,
                },
            }
        elif feature_type == FeatureType.SURF:
            return {
                "extractor": {
                    "hessianThreshold": 400,
                    "nOctaves": 4,
                    "nOctaveLayers": 3,
                    "extended": False,
                    "upright": False,
                },
                "matcher": {
                    "matcher_type": "flann",
                    "algorithm": "kdtree",
                    "index_params": {"algorithm": 1, "trees": 5},
                    "search_params": {"checks": 50},
                    "ratio_threshold": 0.75,
                },
            }
        else:
            raise ValueError(f"不支持的特征类型: {feature_type}")
