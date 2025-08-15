#
# 注意：匹配阶段本身只做度量与初筛；几何一致性在流水线 post_filter 中进行。

# 功能: 定义和实现特征匹配算法。
#
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np
import cv2
import logging
from src.models.frame import FrameFeatures, FrameMatches
from src.models.types import MatchPair

logger = logging.getLogger(__name__)


class FeatureMatcher(ABC):
    """特征匹配器抽象基类"""

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        pass

    @abstractmethod
    def match(self, features1: FrameFeatures, features2: FrameFeatures) -> FrameMatches:
        """匹配两帧的特征"""
        pass


class BruteForceMatcher(FeatureMatcher):
    """暴力匹配器实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化暴力匹配器

        config 参数:
        {
            "normType": cv2.NORM_L2,  # 距离度量类型 (NORM_L2 for SIFT, NORM_HAMMING for ORB)
            "crossCheck": True,  # 是否启用交叉检查
            "ratio_threshold": 0.75,  # Lowe's ratio test 阈值
            "max_distance": None  # 最大匹配距离，None表示不限制
        }
        """
        default_config = {
            "normType": cv2.NORM_L2,
            "crossCheck": True,
            "ratio_threshold": 0.75,
            "max_distance": None,
            "distance_filter": "mad",  # 可选: none|mad
            "mad_k": 3.0,
        }

        self.config = {**default_config, **config}

        try:
            self.matcher = cv2.BFMatcher(
                normType=self.config["normType"], crossCheck=self.config["crossCheck"]
            )
            logger.info(f"初始化暴力匹配器，配置: {self.config}")
        except Exception as e:
            logger.error(f"初始化暴力匹配器失败: {e}")
            raise

    def match(self, features1: FrameFeatures, features2: FrameFeatures) -> FrameMatches:
        """
        匹配两帧的特征

        Args:
            features1: 第一帧的特征
            features2: 第二帧的特征

        Returns:
            FrameMatches: 匹配结果
        """
        if (
            features1.descriptors is None
            or features2.descriptors is None
            or len(features1.keypoints) == 0
            or len(features2.keypoints) == 0
        ):
            logger.debug("特征描述子为空，无法进行匹配")
            return FrameMatches(matches=[], scores=[])

        try:
            if self.config["crossCheck"]:
                # 使用交叉检查的直接匹配
                matches = self.matcher.match(
                    features1.descriptors, features2.descriptors
                )
            else:
                # 使用knnMatch进行Lowe's ratio test
                knn_matches = self.matcher.knnMatch(
                    features1.descriptors, features2.descriptors, k=2
                )
                matches = []
                for m_n in knn_matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        # Lowe's ratio test
                        if m.distance < self.config["ratio_threshold"] * n.distance:
                            matches.append(m)
                    elif len(m_n) == 1:
                        matches.append(m_n[0])

            if not matches:
                logger.debug("未找到任何匹配")
                return FrameMatches(matches=[], scores=[])

            # 过滤距离过大的匹配
            if self.config["max_distance"] is not None:
                matches = [
                    m for m in matches if m.distance <= self.config["max_distance"]
                ]

            # 鲁棒距离分布过滤（MAD）
            if matches and self.config.get("distance_filter", "mad") == "mad":
                d = np.array([m.distance for m in matches], dtype=np.float32)
                med = float(np.median(d))
                mad = float(np.median(np.abs(d - med)) + 1e-6)
                k = float(self.config.get("mad_k", 3.0))
                upper = med + k * 1.4826 * mad
                matches = [m for m in matches if m.distance <= upper]

            # 转换为我们的数据格式
            match_pairs: List[MatchPair] = [(m.queryIdx, m.trainIdx) for m in matches]
            match_scores = [
                1.0 / (1.0 + m.distance) for m in matches
            ]  # 距离转换为相似度分数

            logger.debug(f"找到 {len(matches)} 个有效匹配")

            return FrameMatches(matches=match_pairs, scores=match_scores)

        except Exception as e:
            logger.error(f"特征匹配失败: {e}")
            return FrameMatches(matches=[], scores=[])


class FLANNMatcher(FeatureMatcher):
    """FLANN匹配器实现"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化FLANN匹配器

        config 参数:
        {
            "algorithm": "kdtree",  # 索引算法类型 ("kdtree" for SIFT, "lsh" for ORB)
            "index_params": {...},  # 索引参数
            "search_params": {"checks": 50},  # 搜索参数
            "ratio_threshold": 0.75,  # Lowe's ratio test 阈值
            "max_distance": None  # 最大匹配距离
        }
        """
        default_sift_config = {
            "algorithm": "kdtree",
            "index_params": {"algorithm": 1, "trees": 5},  # FLANN_INDEX_KDTREE
            "search_params": {"checks": 50},
            "ratio_threshold": 0.75,
            "max_distance": None,
        }

        default_orb_config = {
            "algorithm": "lsh",
            "index_params": {
                "algorithm": 6,
                "table_number": 6,
                "key_size": 12,
                "multi_probe_level": 1,
            },
            "search_params": {"checks": 50},
            "ratio_threshold": 0.75,
            "max_distance": None,
        }

        # 根据算法类型选择默认配置
        if config.get("algorithm") == "lsh":
            default_config = default_orb_config
        else:
            default_config = default_sift_config

        self.config = {**default_config, **config}

        try:
            self.matcher = cv2.FlannBasedMatcher(
                self.config["index_params"], self.config["search_params"]
            )
            logger.info(f"初始化FLANN匹配器，配置: {self.config}")
        except Exception as e:
            logger.error(f"初始化FLANN匹配器失败: {e}")
            raise

    def match(self, features1: FrameFeatures, features2: FrameFeatures) -> FrameMatches:
        """
        匹配两帧的特征

        Args:
            features1: 第一帧的特征
            features2: 第二帧的特征

        Returns:
            FrameMatches: 匹配结果
        """
        if (
            features1.descriptors is None
            or features2.descriptors is None
            or len(features1.keypoints) == 0
            or len(features2.keypoints) == 0
        ):
            logger.debug("特征描述子为空，无法进行匹配")
            return FrameMatches(matches=[], scores=[])

        try:
            # KDTree 需要 float32；LSH 使用原始二值（uint8）
            if self.config.get("algorithm") == "lsh":
                desc1 = features1.descriptors
                desc2 = features2.descriptors
            else:
                desc1 = features1.descriptors.astype(np.float32)
                desc2 = features2.descriptors.astype(np.float32)

            # 使用knnMatch进行Lowe's ratio test
            knn_matches = self.matcher.knnMatch(desc1, desc2, k=2)

            matches = []
            for m_n in knn_matches:
                if len(m_n) == 2:
                    m, n = m_n
                    if m.distance < self.config["ratio_threshold"] * n.distance:
                        matches.append(m)
                elif len(m_n) == 1:
                    matches.append(m_n[0])

            if not matches:
                logger.debug("未找到任何匹配")
                return FrameMatches(matches=[], scores=[])

            # 过滤距离过大的匹配
            if self.config["max_distance"] is not None:
                matches = [m for m in matches if m.distance <= self.config["max_distance"]]

            # 鲁棒距离分布过滤（MAD）
            if matches and self.config.get("distance_filter", "mad") == "mad":
                d = np.array([m.distance for m in matches], dtype=np.float32)
                med = float(np.median(d))
                mad = float(np.median(np.abs(d - med)) + 1e-6)
                k = float(self.config.get("mad_k", 3.0))
                upper = med + k * 1.4826 * mad
                matches = [m for m in matches if m.distance <= upper]

            # 转换为我们的数据格式
            match_pairs: List[MatchPair] = [(m.queryIdx, m.trainIdx) for m in matches]
            match_scores = [1.0 / (1.0 + m.distance) for m in matches]

            logger.debug(f"找到 {len(matches)} 个有效匹配")

            return FrameMatches(matches=match_pairs, scores=match_scores)

        except Exception as e:
            logger.error(f"FLANN特征匹配失败: {e}")
            return FrameMatches(matches=[], scores=[])
