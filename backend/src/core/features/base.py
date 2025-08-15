"""
Feature Extractor Base Class

This module defines the abstract interface for feature extraction algorithms
used in visual odometry and SLAM systems. Feature extractors detect and
describe distinctive points in images that can be reliably matched across
different viewpoints.

Feature extraction is a fundamental component of visual odometry pipelines,
providing the local image features that enable camera motion estimation
and 3D scene reconstruction.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import numpy as np
from src.models.frame import FrameFeatures


class FeatureExtractor(ABC):
    """
    Abstract base class for feature extraction algorithms.

    This class defines the interface that all feature extractors must implement
    to ensure consistent behavior across different algorithms (SIFT, ORB, etc.).
    Feature extractors detect keypoints and compute descriptors that characterize
    the local image appearance around each keypoint.

    Key Concepts:
    - **Keypoints**: Distinctive image locations (corners, blobs, edges)
    - **Descriptors**: Numerical vectors describing local image appearance
    - **Repeatability**: Ability to detect same features across viewpoints
    - **Distinctiveness**: Ability to distinguish between different features
    - **Invariance**: Robustness to transformations (scale, rotation, illumination)

    Common Feature Types:
    - **SIFT**: Scale-Invariant Feature Transform (patented, high quality)
    - **ORB**: Oriented FAST and Rotated BRIEF (patent-free, fast)
    - **SURF**: Speeded Up Robust Features (patented, good performance)
    - **AKAZE**: Accelerated-KAZE (patent-free, good quality)

    Attributes:
        config (Dict[str, Any]): Configuration parameters for the extractor

    Example:
        >>> extractor = SIFTExtractor({
        ...     'max_features': 5000,
        ...     'contrast_threshold': 0.04,
        ...     'edge_threshold': 10
        ... })
        >>> features = extractor.extract(image)
        >>> print(f"Extracted {len(features.keypoints)} features")
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the feature extractor with configuration parameters.

        Sets up the feature extraction algorithm with the specified parameters.
        Different algorithms may require different configuration options, but
        common parameters include maximum number of features, detection thresholds,
        and algorithm-specific tuning parameters.

        Args:
            config: Dictionary containing algorithm parameters. Common parameters:
                - max_features (int): Maximum number of features to extract
                    Higher values provide more features but increase computation time.
                    Typical range: 1000-10000 for visual odometry applications.
                - contrast_threshold (float): Minimum contrast for feature detection
                    Lower values detect more features but may include noise.
                    Typical range: 0.01-0.1 depending on image quality.
                - edge_threshold (float): Edge response threshold
                    Higher values filter out edge-like features.
                    Typical range: 5-20 for most applications.

        Example:
            >>> config = {
            ...     'max_features': 5000,        # Extract up to 5000 features
            ...     'contrast_threshold': 0.04,  # Moderate contrast requirement
            ...     'edge_threshold': 10,        # Standard edge filtering
            ...     'sigma': 1.6                 # Algorithm-specific parameter
            ... }
            >>> extractor = ConcreteExtractor(config)

        Note:
            Configuration parameters should be validated in the concrete
            implementation to ensure they are within acceptable ranges
            and compatible with the specific algorithm requirements.
        """
        pass

    @abstractmethod
    def extract(self, image: np.ndarray) -> FrameFeatures:
        """
        Extract keypoints and descriptors from an input image.

        This is the main method that performs feature detection and description.
        It analyzes the input image to find distinctive points and computes
        numerical descriptors that characterize the local appearance around
        each keypoint.

        The extraction process typically involves:
        1. **Detection**: Find keypoint locations using corner/blob detectors
        2. **Orientation**: Determine dominant orientation for rotation invariance
        3. **Description**: Compute descriptor vector characterizing local appearance
        4. **Filtering**: Remove weak or unstable features based on quality metrics

        Args:
            image: Input image as numpy array. Expected formats:
                - Grayscale: (height, width) with dtype uint8
                - Color: (height, width, 3) with dtype uint8 (will be converted)
                - Floating point: Values should be in range [0, 1] or [0, 255]

        Returns:
            FrameFeatures object containing:
                - keypoints: List of detected keypoint locations and properties
                - descriptors: Numpy array of descriptor vectors (N x D)
                - detection_time: Time spent on feature detection (seconds)
                - description_time: Time spent on descriptor computation (seconds)
                - total_features: Total number of features extracted
                - quality_scores: Optional quality/response scores for each feature

        Raises:
            FeatureExtractionError: When feature extraction fails
            ValidationError: When input image format is invalid

        Example:
            >>> # Load and prepare image
            >>> image = cv2.imread('image.jpg', cv2.IMREAD_GRAYSCALE)
            >>>
            >>> # Extract features
            >>> features = extractor.extract(image)
            >>>
            >>> # Access results
            >>> print(f"Extracted {len(features.keypoints)} keypoints")
            >>> print(f"Descriptor shape: {features.descriptors.shape}")
            >>> print(f"Detection time: {features.detection_time:.3f}s")
            >>>
            >>> # Use keypoints for matching
            >>> for i, kp in enumerate(features.keypoints):
            ...     x, y = kp.pt
            ...     descriptor = features.descriptors[i]
            ...     print(f"Keypoint {i}: ({x:.1f}, {y:.1f})")

        Performance Notes:
            - Extraction time scales with image size and max_features parameter
            - Typical performance: 10-100ms for 640x480 images on modern hardware
            - GPU acceleration may be available for some algorithms
            - Consider image preprocessing (denoising, contrast enhancement) for better results

        Quality Considerations:
            - More features generally improve tracking robustness
            - Feature distribution should be reasonably uniform across the image
            - Avoid extracting too many features in small regions (clustering)
            - Balance between feature quantity and computational efficiency
        """
        pass

    @abstractmethod
    def get_descriptor_size(self) -> int:
        """
        Get the dimensionality of the descriptor vectors.

        Returns the number of elements in each descriptor vector produced
        by this feature extractor. This is a fixed value that depends on
        the specific algorithm and its configuration.

        Returns:
            int: Descriptor vector dimensionality. Common values:
                - SIFT: 128 dimensions (standard configuration)
                - ORB: 32 bytes = 256 bits (binary descriptor)
                - SURF: 64 or 128 dimensions (depending on extended flag)
                - BRIEF: 16, 32, or 64 bytes (configurable)

        Example:
            >>> desc_size = extractor.get_descriptor_size()
            >>> print(f"Each descriptor has {desc_size} dimensions")
            >>>
            >>> # Allocate storage for descriptors
            >>> max_features = 5000
            >>> descriptor_storage = np.zeros((max_features, desc_size),
            ...                              dtype=extractor.get_descriptor_type())

        Note:
            This value must be consistent with the descriptors returned by
            the extract() method. It's used for memory allocation and
            compatibility checking in matching algorithms.
        """
        pass

    @abstractmethod
    def get_descriptor_type(self) -> np.dtype:
        """
        Get the numpy data type of the descriptor arrays.

        Returns the numpy dtype used for descriptor storage. This determines
        the memory layout and numerical precision of the descriptors.

        Returns:
            np.dtype: Numpy data type for descriptors. Common types:
                - np.float32: 32-bit floating point (SIFT, SURF)
                - np.uint8: 8-bit unsigned integer (ORB, BRIEF binary descriptors)
                - np.float64: 64-bit floating point (high precision applications)

        Example:
            >>> desc_type = extractor.get_descriptor_type()
            >>> print(f"Descriptors use {desc_type} data type")
            >>>
            >>> # Create compatible storage
            >>> descriptors = np.zeros((1000, extractor.get_descriptor_size()),
            ...                       dtype=desc_type)
            >>>
            >>> # Check memory usage
            >>> bytes_per_desc = desc_type().itemsize * extractor.get_descriptor_size()
            >>> print(f"Each descriptor uses {bytes_per_desc} bytes")

        Memory Considerations:
            - float32: 4 bytes per element, good precision/memory balance
            - uint8: 1 byte per element, compact but limited precision
            - Binary descriptors (uint8): Very compact, fast matching
            - float64: 8 bytes per element, high precision but large memory footprint

        Matching Compatibility:
            - Floating point descriptors: Use L2 (Euclidean) distance
            - Binary descriptors: Use Hamming distance
            - Ensure matcher algorithm matches descriptor type
        """
        pass

    def validate_image(self, image: np.ndarray) -> np.ndarray:
        """
        Validate and preprocess input image for feature extraction.

        Performs validation and basic preprocessing of the input image to
        ensure it's in the correct format for feature extraction.

        Args:
            image: Input image array

        Returns:
            np.ndarray: Validated and preprocessed image

        Raises:
            ValidationError: If image format is invalid
        """
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be a numpy array")

        if image.size == 0:
            raise ValueError("Image cannot be empty")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            if image.shape[2] == 3:
                # Convert BGR to grayscale (OpenCV convention)
                image = np.dot(image[..., :3], [0.114, 0.587, 0.299])
            elif image.shape[2] == 1:
                image = image.squeeze(axis=2)

        # Ensure uint8 format
        if image.dtype != np.uint8:
            if image.dtype in [np.float32, np.float64]:
                # Assume normalized values [0, 1] or [0, 255]
                if image.max() <= 1.0:
                    image = (image * 255).astype(np.uint8)
                else:
                    image = image.astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        return image

    def get_algorithm_name(self) -> str:
        """
        Get the name of the feature extraction algorithm.

        Returns:
            str: Algorithm name (e.g., 'SIFT', 'ORB', 'SURF')
        """
        return self.__class__.__name__.replace("Extractor", "").upper()

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.

        Returns:
            Dict[str, Any]: Configuration summary for logging/debugging
        """
        return {
            "algorithm": self.get_algorithm_name(),
            "descriptor_size": self.get_descriptor_size(),
            "descriptor_type": str(self.get_descriptor_type()),
            "config": getattr(self, "config", {}),
        }
