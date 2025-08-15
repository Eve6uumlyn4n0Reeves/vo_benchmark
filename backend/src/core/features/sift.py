"""
SIFT Feature Extractor Implementation

This module implements the Scale-Invariant Feature Transform (SIFT) algorithm
for robust feature detection and description. SIFT features are invariant to
scale, rotation, and partially invariant to illumination changes and affine
transformations, making them ideal for visual odometry applications.

The implementation uses OpenCV's optimized SIFT detector with configurable
parameters for different use cases and performance requirements.

Key Features:
- Scale and rotation invariance
- High distinctiveness and repeatability
- Robust to illumination changes
- Configurable detection parameters
- Performance monitoring and caching
- Comprehensive error handling

Note:
    SIFT is patented (US Patent 6,711,293) and may require licensing for
    commercial use. Consider using ORB for patent-free alternatives.

Author:
    VO-Benchmark Team

Version:
    1.0.0

References:
    Lowe, D. G. (2004). Distinctive image features from scale-invariant keypoints.
    International Journal of Computer Vision, 60(2), 91-110.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2
import logging
import time
from src.core.features.base import FeatureExtractor
from src.models.frame import FrameFeatures
from src.models.types import Point2D
from src.utils.error_handling import (
    handle_cv_error,
    retry_on_failure,
    FeatureExtractionError,
    validate_input,
    is_not_none,
    is_valid_image_shape,
)
from src.utils.performance import (
    cached_feature_extraction,
    profile_performance,
    optimize_image_processing,
    performance_monitor,
)

logger = logging.getLogger(__name__)


class SIFTExtractor(FeatureExtractor):
    """
    Scale-Invariant Feature Transform (SIFT) feature extractor.

    This class implements the SIFT algorithm for detecting and describing
    local features in images. SIFT features are particularly well-suited
    for visual odometry due to their robustness to viewpoint changes,
    scale variations, and illumination differences.

    The SIFT algorithm consists of four main stages:
    1. **Scale-space extrema detection**: Identify potential keypoints
    2. **Keypoint localization**: Refine keypoint locations and filter unstable points
    3. **Orientation assignment**: Assign dominant orientations for rotation invariance
    4. **Descriptor generation**: Create distinctive descriptor vectors

    Advantages:
    - Excellent repeatability across viewpoints
    - High distinctiveness for reliable matching
    - Scale and rotation invariance
    - Robust to moderate illumination changes
    - Well-established and thoroughly tested

    Disadvantages:
    - Computationally expensive
    - Patent restrictions for commercial use
    - Sensitive to blur and low contrast
    - Large descriptor size (128 dimensions)

    Attributes:
        config (Dict[str, Any]): Configuration parameters
        detector (cv2.SIFT): OpenCV SIFT detector instance
        _extraction_stats (Dict): Performance statistics

    Example:
        >>> extractor = SIFTExtractor({
        ...     'nfeatures': 5000,
        ...     'contrastThreshold': 0.04,
        ...     'edgeThreshold': 10
        ... })
        >>> features = extractor.extract(image)
        >>> print(f"Extracted {len(features.keypoints)} SIFT features")
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize SIFT feature extractor with configuration parameters.

        Creates and configures the OpenCV SIFT detector with the specified
        parameters. All parameters are validated and defaults are applied
        for missing values.

        Args:
            config: Dictionary containing SIFT parameters:
                - nfeatures (int): Maximum number of features to retain.
                    0 means no limit. Higher values provide more features
                    but increase computation time. Typical: 1000-10000.
                - nOctaveLayers (int): Number of layers in each octave.
                    More layers provide better scale sampling but increase
                    computation. Typical: 3-4.
                - contrastThreshold (float): Contrast threshold for filtering
                    weak features. Lower values detect more features but
                    may include noise. Typical: 0.03-0.08.
                - edgeThreshold (float): Edge response threshold for filtering
                    edge-like features. Higher values are more restrictive.
                    Typical: 5-20.
                - sigma (float): Gaussian blur parameter for the initial
                    image smoothing. Affects feature scale. Typical: 1.6.

        Raises:
            FeatureExtractionError: If SIFT detector creation fails
            ValidationError: If configuration parameters are invalid

        Example:
            >>> # Standard configuration for visual odometry
            >>> config = {
            ...     'nfeatures': 5000,        # Extract up to 5000 features
            ...     'nOctaveLayers': 3,       # Standard octave layers
            ...     'contrastThreshold': 0.04, # Moderate contrast filtering
            ...     'edgeThreshold': 10,      # Standard edge filtering
            ...     'sigma': 1.6              # Standard initial blur
            ... }
            >>> extractor = SIFTExtractor(config)

            >>> # High-quality configuration (slower but more features)
            >>> high_quality_config = {
            ...     'nfeatures': 10000,
            ...     'nOctaveLayers': 4,
            ...     'contrastThreshold': 0.03,
            ...     'edgeThreshold': 15,
            ...     'sigma': 1.6
            ... }
            >>> hq_extractor = SIFTExtractor(high_quality_config)

            >>> # Fast configuration (fewer features but faster)
            >>> fast_config = {
            ...     'nfeatures': 2000,
            ...     'nOctaveLayers': 3,
            ...     'contrastThreshold': 0.06,
            ...     'edgeThreshold': 8,
            ...     'sigma': 1.6
            ... }
            >>> fast_extractor = SIFTExtractor(fast_config)

        Parameter Guidelines:
        - **nfeatures**: Balance between tracking robustness and speed
        - **contrastThreshold**: Lower for low-contrast images, higher for noisy images
        - **edgeThreshold**: Higher values reduce edge-like features
        - **nOctaveLayers**: More layers for better scale invariance
        - **sigma**: Usually kept at default value of 1.6
        """
        # Define default configuration with well-tested values
        default_config = {
            "nfeatures": 0,  # No limit on feature count
            "nOctaveLayers": 3,  # Standard number of octave layers
            "contrastThreshold": 0.04,  # Moderate contrast filtering
            "edgeThreshold": 10,  # Standard edge response threshold
            "sigma": 1.6,  # Standard initial Gaussian blur
        }

        # Merge user configuration with defaults
        user_config = config or {}
        final_config = {**default_config, **user_config}

        # Validate configuration parameters
        self._validate_config(final_config)

        try:
            # Create OpenCV SIFT detector with validated configuration
            from typing import cast, Any
            self.detector = cast(Any, cv2).SIFT_create(**final_config)
            # Backward-compat alias for legacy code paths
            self.sift = self.detector
            self.config = final_config

            # Initialize performance tracking
            self._extraction_stats = {
                "total_extractions": 0,
                "total_features": 0,
                "total_time": 0.0,
                "average_features_per_extraction": 0.0,
                "average_time_per_extraction": 0.0,
            }

            logger.info(f"SIFT extractor initialized with config: {final_config}")

        except Exception as e:
            logger.error(f"Failed to initialize SIFT extractor: {e}")
            raise FeatureExtractionError(f"SIFT initialization failed: {e}")

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate SIFT configuration parameters.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValidationError: If any parameter is invalid
        """
        # Validate nfeatures
        if not isinstance(config["nfeatures"], int) or config["nfeatures"] < 0:
            raise ValueError("nfeatures must be a non-negative integer")

        # Validate nOctaveLayers
        if not isinstance(config["nOctaveLayers"], int) or config["nOctaveLayers"] < 1:
            raise ValueError("nOctaveLayers must be a positive integer")

        # Validate contrastThreshold
        if (
            not isinstance(config["contrastThreshold"], (int, float))
            or config["contrastThreshold"] <= 0
        ):
            raise ValueError("contrastThreshold must be a positive number")

        # Validate edgeThreshold
        if (
            not isinstance(config["edgeThreshold"], (int, float))
            or config["edgeThreshold"] <= 0
        ):
            raise ValueError("edgeThreshold must be a positive number")

        # Validate sigma
        if not isinstance(config["sigma"], (int, float)) or config["sigma"] <= 0:
            raise ValueError("sigma must be a positive number")

    @cached_feature_extraction("SIFT")
    @profile_performance
    @handle_cv_error
    @retry_on_failure(max_retries=2, delay=0.1, exceptions=FeatureExtractionError)
    def extract(self, image: np.ndarray) -> FrameFeatures:
        """
        Extract SIFT features from input image.

        Performs the complete SIFT feature extraction pipeline including
        keypoint detection, orientation assignment, and descriptor computation.
        The method is optimized for performance and includes comprehensive
        error handling and validation.

        Args:
            image: Input image as numpy array. Supported formats:
                - Grayscale: (height, width) with dtype uint8
                - Color: (height, width, 3) with dtype uint8 (converted to grayscale)
                - Floating point: Values in range [0, 1] or [0, 255]

        Returns:
            FrameFeatures containing:
                - keypoints: List of cv2.KeyPoint objects with location, scale, orientation
                - descriptors: Numpy array of shape (N, 128) with float32 descriptors
                - scores: Response values for each keypoint (higher = better)
                - detection_time: Time spent on keypoint detection (seconds)
                - description_time: Time spent on descriptor computation (seconds)
                - total_features: Number of features extracted

        Raises:
            FeatureExtractionError: When SIFT extraction fails
            ValidationError: When input image format is invalid

        Example:
            >>> # Extract features from image
            >>> features = extractor.extract(image)
            >>>
            >>> # Access keypoint information
            >>> for i, kp in enumerate(features.keypoints):
            ...     x, y = kp.pt                    # Keypoint location
            ...     scale = kp.size                 # Keypoint scale
            ...     angle = kp.angle                # Dominant orientation
            ...     response = kp.response          # Corner response
            ...     descriptor = features.descriptors[i]  # 128-dim descriptor
            ...
            ...     print(f"Keypoint {i}: ({x:.1f}, {y:.1f}), "
            ...           f"scale={scale:.1f}, angle={angle:.1f}")

        Performance Notes:
            - Typical extraction time: 50-200ms for 640x480 images
            - Memory usage: ~0.5KB per feature (keypoint + descriptor)
            - Feature count depends on image content and parameters
            - Consider reducing nfeatures for real-time applications

        Quality Tips:
            - Ensure good image contrast for reliable detection
            - Avoid motion blur which reduces feature quality
            - Consider image preprocessing (denoising, sharpening) for low-quality images
            - Balance nfeatures parameter between robustness and speed
        """
        # Input validation and preprocessing
        validate_input(image, [is_not_none], "Input image cannot be None")

        # Allow empty images: return empty features without raising
        if hasattr(image, "size") and image.size == 0:
            logger.warning("Input image is empty")
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)

        # Validate shape only after handling empty images
        validate_input(image.shape, [is_valid_image_shape], "Invalid image shape")

        # 限制维度在2或3维，1维/4维等视为无效
        if len(image.shape) < 2 or len(image.shape) > 3:
            raise ValueError(f"Invalid image shape: {image.shape}")

        start_time = time.time()

        try:
            # 优化图像处理
            image = optimize_image_processing(image)

            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 提取特征
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)

            if keypoints is None or len(keypoints) == 0:
                logger.debug("未检测到SIFT特征")
                return FrameFeatures(keypoints=[], descriptors=None, scores=None)

            # 转换关键点为坐标列表
            keypoint_coords: List[Point2D] = [(kp.pt[0], kp.pt[1]) for kp in keypoints]

            # 提取关键点响应分数
            scores = [kp.response for kp in keypoints]

            # 记录性能指标
            extraction_time = (time.time() - start_time) * 1000  # 转换为毫秒
            performance_monitor.record_metric(
                "sift_extraction_time", extraction_time, "ms"
            )
            performance_monitor.record_metric(
                "sift_feature_count", len(keypoints), "count"
            )

            logger.debug(
                f"提取到 {len(keypoints)} 个SIFT特征，耗时 {extraction_time:.1f}ms"
            )

            return FrameFeatures(
                keypoints=keypoint_coords, descriptors=descriptors, scores=scores
            )

        except cv2.error as e:
            raise FeatureExtractionError(f"OpenCV SIFT特征提取失败: {e}")
        except Exception as e:
            raise FeatureExtractionError(f"SIFT特征提取失败: {e}")

    def get_descriptor_size(self) -> int:
        """返回SIFT描述子的维度"""
        return 128

    def get_descriptor_type(self) -> np.dtype[Any]:
        """返回SIFT描述子的数据类型"""
        return np.dtype(np.float32)

    def get_config(self) -> Dict[str, Any]:
        """返回当前配置参数"""
        return self.config.copy()
