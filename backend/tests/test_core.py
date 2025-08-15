#
# 功能: 核心功能测试
#
import pytest
import numpy as np
import cv2
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.features.sift import SIFTExtractor
from src.core.features.orb import ORBExtractor
from src.core.features.matcher import BruteForceMatcher, FLANNMatcher
from src.core.ransac.standard import StandardRANSAC
from src.core.ransac.prosac import PROSAC
from src.models.frame import FrameFeatures, FrameMatches

class TestFeatureExtraction:
    """特征提取测试类"""
    
    @pytest.fixture
    def test_image(self):
        """创建测试图像"""
        # 创建一个简单的测试图像
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 添加一些特征点（矩形和圆形）
        cv2.rectangle(image, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.circle(image, (400, 300), 50, (255, 255, 255), -1)
        cv2.rectangle(image, (300, 50), (350, 100), (255, 255, 255), -1)
        
        return image
    
    def test_sift_extraction(self, test_image):
        """测试SIFT特征提取"""
        extractor = SIFTExtractor({})
        features = extractor.extract(test_image)
        
        assert isinstance(features, FrameFeatures)
        assert len(features.keypoints) > 0
        assert features.descriptors is not None
        assert features.descriptors.shape[0] == len(features.keypoints)
        assert features.descriptors.shape[1] == 128  # SIFT描述子维度
    
    def test_orb_extraction(self, test_image):
        """测试ORB特征提取"""
        extractor = ORBExtractor({})
        features = extractor.extract(test_image)
        
        assert isinstance(features, FrameFeatures)
        assert len(features.keypoints) > 0
        assert features.descriptors is not None
        assert features.descriptors.shape[0] == len(features.keypoints)
        assert features.descriptors.shape[1] == 32  # ORB描述子维度
    
    def test_sift_parameters(self):
        """测试SIFT参数设置"""
        params = {
            'nfeatures': 1000,
            'contrastThreshold': 0.04,
            'edgeThreshold': 10
        }
        extractor = SIFTExtractor(params)
        
        # 验证参数设置
        assert extractor.config['nfeatures'] == 1000
        assert extractor.config['contrastThreshold'] == 0.04
    
    def test_orb_parameters(self):
        """测试ORB参数设置"""
        params = {
            'nfeatures': 2000,
            'scaleFactor': 1.2,
            'nlevels': 8
        }
        extractor = ORBExtractor(params)
        
        # 验证参数设置
        assert extractor.config['nfeatures'] == 2000
        assert extractor.config['scaleFactor'] == 1.2

class TestFeatureMatching:
    """特征匹配测试类"""
    
    @pytest.fixture
    def sift_features(self, test_image):
        """创建SIFT特征"""
        extractor = SIFTExtractor({})
        return extractor.extract(test_image)

    @pytest.fixture
    def orb_features(self, test_image):
        """创建ORB特征"""
        extractor = ORBExtractor({})
        return extractor.extract(test_image)
    
    @pytest.fixture
    def test_image(self):
        """创建测试图像"""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(image, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.circle(image, (400, 300), 50, (255, 255, 255), -1)
        return image
    
    def test_brute_force_matching_sift(self, sift_features):
        """测试SIFT特征的暴力匹配"""
        matcher = BruteForceMatcher({})
        
        # 使用相同特征进行匹配（应该有很多匹配）
        matches = matcher.match(sift_features, sift_features)
        
        assert isinstance(matches, FrameMatches)
        assert len(matches.matches) > 0
        assert len(matches.scores) == len(matches.matches)
    
    def test_brute_force_matching_orb(self, orb_features):
        """测试ORB特征的暴力匹配"""
        matcher = BruteForceMatcher({'norm_type': cv2.NORM_HAMMING})
        
        # 使用相同特征进行匹配
        matches = matcher.match(orb_features, orb_features)
        
        assert isinstance(matches, FrameMatches)
        assert len(matches.matches) > 0
    
    def test_flann_matching_sift(self, sift_features):
        """测试SIFT特征的FLANN匹配"""
        matcher = FLANNMatcher({})
        
        # 需要足够的特征点才能使用FLANN
        if len(sift_features.keypoints) >= 2:
            matches = matcher.match(sift_features, sift_features)
            assert isinstance(matches, FrameMatches)
            assert len(matches.matches) > 0
    
    def test_matching_parameters(self):
        """测试匹配参数"""
        params = {'ratio_threshold': 0.8}
        matcher = BruteForceMatcher(params)
        
        assert matcher.config['ratio_threshold'] == 0.8

class TestRANSAC:
    """RANSAC测试类"""
    
    @pytest.fixture
    def camera_matrix(self):
        """创建相机内参矩阵"""
        return np.array([
            [525.0, 0.0, 320.0],
            [0.0, 525.0, 240.0],
            [0.0, 0.0, 1.0]
        ])
    
    @pytest.fixture
    def test_matches(self):
        """创建测试匹配点"""
        # 创建一些对应点
        keypoints1 = [(100, 100), (200, 150), (300, 200), (150, 250), (250, 300)]
        keypoints2 = [(105, 102), (205, 152), (305, 202), (155, 252), (255, 302)]  # 稍微偏移
        
        matches = [(i, i) for i in range(len(keypoints1))]
        scores = [0.9] * len(matches)
        
        return FrameMatches(matches=matches, scores=scores), keypoints1, keypoints2
    
    def test_standard_ransac(self, test_matches, camera_matrix):
        """测试标准RANSAC"""
        matches, keypoints1, keypoints2 = test_matches
        
        estimator = StandardRANSAC({
            'threshold': 1.0,
            'confidence': 0.99,
            'max_iters': 1000
        })
        
        result = estimator.estimate(keypoints1, keypoints2, matches, camera_matrix)
        
        # 验证结果结构
        assert result is not None
        assert hasattr(result, 'inlier_mask')
        assert hasattr(result, 'num_iterations')
        assert hasattr(result, 'confidence')
    
    def test_prosac(self, test_matches, camera_matrix):
        """测试PROSAC"""
        matches, keypoints1, keypoints2 = test_matches
        
        estimator = PROSAC({
            'threshold': 1.0,
            'confidence': 0.99,
            'max_iters': 1000
        })
        
        result = estimator.estimate(keypoints1, keypoints2, matches, camera_matrix)
        
        # 验证结果结构
        assert result is not None
        assert hasattr(result, 'inlier_mask')
        assert hasattr(result, 'num_iterations')
    
    def test_ransac_parameters(self):
        """测试RANSAC参数"""
        params = {
            'threshold': 2.0,
            'confidence': 0.999,
            'max_iters': 2000
        }
        
        estimator = StandardRANSAC(params)
        assert estimator.config['threshold'] == 2.0
        assert estimator.config['confidence'] == 0.999
        assert estimator.config['max_iters'] == 2000

class TestFactories:
    """工厂类测试"""
    
    def test_feature_factory(self):
        """测试特征工厂"""
        from src.core.features.factory import FeatureFactory
        from src.models.types import FeatureType
        
        # 测试SIFT创建
        sift_extractor = FeatureFactory.create_extractor(FeatureType.SIFT, {})
        assert isinstance(sift_extractor, SIFTExtractor)

        # 测试ORB创建
        orb_extractor = FeatureFactory.create_extractor(FeatureType.ORB, {})
        assert isinstance(orb_extractor, ORBExtractor)

        # 测试匹配器创建
        matcher = FeatureFactory.create_matcher(FeatureType.SIFT, {})
        assert matcher is not None
    
    def test_ransac_factory(self):
        """测试RANSAC工厂"""
        from src.core.ransac.factory import RANSACFactory
        from src.models.types import RANSACType
        
        # 测试标准RANSAC创建
        standard_ransac = RANSACFactory.create_estimator(RANSACType.STANDARD, {})
        assert isinstance(standard_ransac, StandardRANSAC)

        # 测试PROSAC创建
        prosac = RANSACFactory.create_estimator(RANSACType.PROSAC, {})
        assert isinstance(prosac, PROSAC)

class TestIntegration:
    """集成测试类"""
    
    def test_full_pipeline(self):
        """测试完整的处理流水线"""
        from src.pipeline.processor import FrameProcessor
        from src.core.features.factory import FeatureFactory
        from src.core.ransac.factory import RANSACFactory
        from src.models.types import FeatureType, RANSACType
        
        # 创建测试图像
        image1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(image1, (100, 100), (200, 200), (255, 255, 255), -1)
        
        image2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(image2, (105, 105), (205, 205), (255, 255, 255), -1)  # 稍微移动
        
        # 创建相机内参
        camera_matrix = np.array([
            [525.0, 0.0, 320.0],
            [0.0, 525.0, 240.0],
            [0.0, 0.0, 1.0]
        ])
        
        # 创建处理器组件
        extractor = FeatureFactory.create_extractor(FeatureType.SIFT, {})
        matcher = FeatureFactory.create_matcher(FeatureType.SIFT, {})
        estimator = RANSACFactory.create_estimator(RANSACType.STANDARD, {})
        
        # 创建帧处理器
        processor = FrameProcessor(extractor, matcher, estimator, camera_matrix)
        
        # 处理帧对
        result = processor.process_frame_pair(image1, image2, 1, 0.1)
        
        # 验证结果
        assert result is not None
        assert result.frame_id == 1
        assert result.timestamp == 0.1
        assert result.processing_time > 0

if __name__ == '__main__':
    pytest.main([__file__])
