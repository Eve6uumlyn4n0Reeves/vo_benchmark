#
# 功能: 创建RANSAC估计器的工厂。
#
from typing import Dict, Any, List
import cv2
import logging
from src.models.types import RANSACType
from src.core.ransac.base import RANSACEstimator
from src.core.ransac.standard import StandardRANSAC
from src.core.ransac.prosac import PROSACRANSAC as ProsacEstimator
from src.core.ransac.usac import USACEstimator

logger = logging.getLogger(__name__)


class RANSACFactory:
    """RANSAC估计器工厂类"""

    @staticmethod
    def create_estimator(
        ransac_type: RANSACType, config: Dict[str, Any]
    ) -> RANSACEstimator:
        """
        根据RANSAC类型创建估计器实例

        Args:
            ransac_type: RANSAC算法类型 (STANDARD/PROSAC)
            config: 估计器配置参数

        Returns:
            RANSACEstimator: RANSAC估计器实例

        Raises:
            ValueError: 不支持的RANSAC类型
        """
        try:
            if ransac_type == RANSACType.STANDARD:
                logger.info(f"创建标准RANSAC估计器，配置: {config}")
                return StandardRANSAC(config)
            elif ransac_type == RANSACType.PROSAC:
                logger.info(f"创建PROSAC估计器，配置: {config}")
                return ProsacEstimator(config)
            elif ransac_type in (RANSACType.USAC_DEFAULT, RANSACType.USAC_MAGSAC, RANSACType.USAC_ACCURATE, RANSACType.RHO, RANSACType.LMEDS):
                # Map enum to OpenCV method constant
                method_map = {
                    RANSACType.USAC_DEFAULT: cv2.USAC_DEFAULT,
                    RANSACType.USAC_MAGSAC: cv2.USAC_MAGSAC,
                    RANSACType.USAC_ACCURATE: cv2.USAC_ACCURATE,
                    RANSACType.RHO: cv2.RHO,
                    RANSACType.LMEDS: cv2.LMEDS,
                }
                cfg = {**config, "method": method_map[ransac_type]}
                logger.info(f"创建USAC估计器({ransac_type.value})，配置: {cfg}")
                return USACEstimator(cfg)
            else:
                raise ValueError(f"不支持的RANSAC类型: {ransac_type}")
        except Exception as e:
            logger.error(f"创建RANSAC估计器失败: {e}")
            raise

    @staticmethod
    def get_supported_types() -> List[str]:
        """返回支持的RANSAC类型列表"""
        return [t.value for t in RANSACType]

    @staticmethod
    def get_default_config(ransac_type: RANSACType) -> Dict[str, Any]:
        """
        获取指定RANSAC类型的默认配置

        Args:
            ransac_type: RANSAC类型

        Returns:
            Dict[str, Any]: 默认配置参数
        """
        base_config = {"threshold": 1.0, "confidence": 0.999, "max_iters": 2000}

        if ransac_type == RANSACType.STANDARD:
            return {**base_config, "method": cv2.RANSAC}
        elif ransac_type == RANSACType.PROSAC:
            return {**base_config, "method": cv2.USAC_PROSAC}
        else:
            raise ValueError(f"不支持的RANSAC类型: {ransac_type}")

    @staticmethod
    def get_method_info() -> Dict[str, Dict[str, Any]]:
        """
        获取各种RANSAC方法的详细信息

        Returns:
            Dict: 包含各种方法信息的字典
        """
        return {
            "STANDARD": {
                "description": "标准RANSAC算法，使用随机采样",
                "advantages": ["简单、可靠", "适用于各种场景"],
                "disadvantages": ["收敛速度较慢", "对异常值敏感"],
                "best_for": ["一般用途", "匹配质量不确定的场景"],
                "min_samples": 5,
            },
            "PROSAC": {
                "description": "渐进采样一致性算法，利用匹配质量排序",
                "advantages": ["收敛速度快", "更好的鲁棒性", "利用先验信息"],
                "disadvantages": ["依赖匹配质量排序", "实现复杂度高"],
                "best_for": ["高质量特征匹配", "实时应用场景"],
                "min_samples": 5,
            },
        }
