#
# 功能: 实现ORB特征提取器。
#
from typing import Dict, Any, List
import numpy as np
import cv2
import logging
from src.core.features.base import FeatureExtractor
from src.models.frame import FrameFeatures
from src.models.types import Point2D

logger = logging.getLogger(__name__)


class ORBExtractor(FeatureExtractor):
    """基于OpenCV的ORB特征提取器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化ORB特征提取器

        config 参数:
        {
            "nfeatures": 5000,  # 最大特征数量
            "scaleFactor": 1.2,  # 金字塔抽取比例
            "nlevels": 8,  # 金字塔层数
            "edgeThreshold": 31,  # 边缘尺寸
            "firstLevel": 0,  # 第一层级别
            "WTA_K": 2,  # 每个描述子元素比较的点数
            "scoreType": cv2.ORB_HARRIS_SCORE,  # 特征点评分方法
            "patchSize": 31,  # 描述子周围邻域大小
            "fastThreshold": 20  # FAST角点检测阈值
        }
        """
        # 设置默认参数
        default_config = {
            "nfeatures": 5000,
            "scaleFactor": 1.2,
            "nlevels": 8,
            "edgeThreshold": 31,
            "firstLevel": 0,
            "WTA_K": 2,
            "scoreType": cv2.ORB_HARRIS_SCORE,
            "patchSize": 31,
            "fastThreshold": 20,
        }

        # 更新配置参数
        final_config = {**default_config, **config}

        try:
            from typing import cast, Any
            self.orb = cast(Any, cv2).ORB_create(**final_config)
            self.config = final_config
            logger.info(f"初始化ORB提取器，配置: {final_config}")
        except Exception as e:
            logger.error(f"初始化ORB提取器失败: {e}")
            raise

    def extract(self, image: np.ndarray) -> FrameFeatures:
        """
        从输入图像中提取ORB特征

        Args:
            image: 输入图像 (H, W, 3) 或 (H, W)

        Returns:
            FrameFeatures: 包含关键点、描述子和分数的特征结果
        """
        if image is None or image.size == 0:
            logger.warning("输入图像为空")
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)

        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 检查图像有效性
            if gray.dtype != np.uint8:
                gray = (
                    (gray * 255).astype(np.uint8)
                    if gray.max() <= 1.0
                    else gray.astype(np.uint8)
                )

            # 提取特征
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)

            if keypoints is None or len(keypoints) == 0:
                logger.debug("未检测到ORB特征")
                return FrameFeatures(keypoints=[], descriptors=None, scores=None)

            # 转换关键点为坐标列表
            keypoint_coords: List[Point2D] = [(kp.pt[0], kp.pt[1]) for kp in keypoints]

            # 提取关键点响应分数
            scores = [kp.response for kp in keypoints]

            logger.debug(f"提取到 {len(keypoints)} 个ORB特征")

            return FrameFeatures(
                keypoints=keypoint_coords, descriptors=descriptors, scores=scores
            )

        except Exception as e:
            logger.error(f"ORB特征提取失败: {e}")
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)

    def get_descriptor_size(self) -> int:
        """返回ORB描述子的维度"""
        return 32

    def get_descriptor_type(self) -> np.dtype[Any]:
        """返回ORB描述子的数据类型"""
        return np.dtype(np.uint8)

    def get_config(self) -> Dict[str, Any]:
        """返回当前配置参数"""
        return self.config.copy()
