"""特征处理模块 - 特征提取和匹配

提供SIFT、ORB等特征提取器和对应的匹配器实现。
"""

from src.core.features.base import FeatureExtractor
from src.core.features.sift import SIFTExtractor
from src.core.features.orb import ORBExtractor
from src.core.features.matcher import FeatureMatcher, BruteForceMatcher, FLANNMatcher
from src.core.features.factory import FeatureFactory

__all__ = [
    "FeatureExtractor",
    "FeatureMatcher",
    "SIFTExtractor",
    "ORBExtractor",
    "BruteForceMatcher",
    "FLANNMatcher",
    "FeatureFactory",
]
