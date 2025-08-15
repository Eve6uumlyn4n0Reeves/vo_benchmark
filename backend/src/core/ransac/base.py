"""
RANSAC Essential Matrix Estimator Base Class

This module defines the abstract interface for RANSAC-based essential matrix
estimation algorithms used in visual odometry. The essential matrix encodes
the epipolar geometry between two camera views and is fundamental for
pose estimation in stereo vision systems.

The RANSAC (Random Sample Consensus) framework provides robust estimation
in the presence of outliers, which are common in feature matching due to
mismatches, repetitive patterns, and dynamic objects.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
from src.models.types import Point2D
from src.models.frame import FrameMatches, RANSACResult


class RANSACEstimator(ABC):
    """
    Abstract base class for RANSAC essential matrix estimators.

    This class defines the interface that all RANSAC-based essential matrix
    estimators must implement. It provides a consistent API for different
    RANSAC variants (Standard RANSAC, PROSAC, etc.) while allowing for
    algorithm-specific optimizations.

    The essential matrix E relates corresponding points in two images:
    x2^T * E * x1 = 0, where x1 and x2 are homogeneous coordinates.

    Key Concepts:
    - **Essential Matrix**: Encodes camera motion (rotation + translation)
    - **Epipolar Constraint**: Geometric relationship between corresponding points
    - **RANSAC**: Robust estimation framework for handling outliers
    - **Inliers**: Point correspondences consistent with the estimated model
    - **Outliers**: Mismatched or erroneous point correspondences

    Attributes:
        config (Dict[str, Any]): Configuration parameters for the estimator

    Example:
        >>> estimator = StandardRANSAC({
        ...     'threshold': 1.0,
        ...     'confidence': 0.999,
        ...     'max_iters': 2000
        ... })
        >>> result = estimator.estimate(kpts1, kpts2, matches, camera_matrix)
        >>> if result.success:
        ...     print(f"Found {result.num_inliers} inliers")
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RANSAC estimator with configuration parameters.

        Args:
            config: Dictionary containing algorithm parameters:
                - threshold (float): Inlier threshold in pixels (default: 1.0)
                    Maximum distance from epipolar line for a point to be
                    considered an inlier. Smaller values are more restrictive.
                - confidence (float): Desired confidence level (default: 0.999)
                    Probability that at least one sample is outlier-free.
                    Higher values require more iterations but increase reliability.
                - max_iters (int): Maximum RANSAC iterations (default: 2000)
                    Upper bound on iterations to prevent infinite loops.
                    Actual iterations may be lower if convergence is achieved.

        Example:
            >>> config = {
            ...     "threshold": 1.0,      # 1 pixel inlier threshold
            ...     "confidence": 0.999,   # 99.9% confidence
            ...     "max_iters": 2000      # Maximum 2000 iterations
            ... }
            >>> estimator = ConcreteRANSAC(config)

        Note:
            The threshold should be chosen based on image resolution and
            expected accuracy. For high-resolution images, smaller thresholds
            (0.5-1.0 pixels) are appropriate. For lower resolution or noisy
            images, larger thresholds (1.0-2.0 pixels) may be necessary.
        """
        pass

    @abstractmethod
    def estimate(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
        K: np.ndarray,
    ) -> RANSACResult:
        """
        Estimate essential matrix using RANSAC from matched keypoints.

        This method implements the core RANSAC algorithm for robust essential
        matrix estimation. It iteratively samples minimal sets of correspondences,
        estimates candidate models, and evaluates their support to find the
        best model that explains the most inliers.

        Algorithm Overview:
        1. Sample minimal set of correspondences (5 or 8 points)
        2. Estimate essential matrix from sample
        3. Evaluate all correspondences against the model
        4. Count inliers within threshold distance
        5. Keep best model with most inliers
        6. Repeat until convergence or max iterations
        7. Refine final model using all inliers

        Args:
            keypoints1: List of keypoints from first image as (x, y) coordinates.
                       Should be in pixel coordinates, not normalized.
            keypoints2: List of keypoints from second image as (x, y) coordinates.
                       Must correspond to keypoints1 via matches parameter.
            matches: Validated matches between keypoints with confidence scores.
                    Contains indices into keypoints1 and keypoints2 arrays.
            K: Camera intrinsic matrix as 3x3 numpy array:
               [[fx,  0, cx],
                [ 0, fy, cy],
                [ 0,  0,  1]]
               Used to normalize pixel coordinates to camera coordinates.

        Returns:
            RANSACResult containing:
                - essential_matrix: 3x3 essential matrix (np.ndarray)
                - rotation: 3x3 rotation matrix from camera 1 to camera 2
                - translation: 3x1 translation vector (unit length)
                - inlier_mask: Boolean array indicating inlier correspondences
                - num_inliers: Number of inlier correspondences (int)
                - iterations: Actual RANSAC iterations performed (int)
                - success: Whether estimation succeeded (bool)
                - inlier_ratio: Fraction of correspondences that are inliers
                - reprojection_error: Average reprojection error of inliers

        Raises:
            RANSACError: When insufficient matches or estimation fails
            ValidationError: When input parameters are invalid

        Example:
            >>> # Prepare input data
            >>> kpts1 = [(100, 150), (200, 250), ...]  # Pixel coordinates
            >>> kpts2 = [(105, 155), (195, 245), ...]  # Corresponding points
            >>> matches = FrameMatches(...)             # Validated matches
            >>> K = np.array([[800, 0, 320],           # Camera matrix
            ...               [0, 800, 240],
            ...               [0, 0, 1]])
            >>>
            >>> # Estimate essential matrix
            >>> result = estimator.estimate(kpts1, kpts2, matches, K)
            >>>
            >>> # Check results
            >>> if result.success:
            ...     print(f"Essential matrix estimated successfully")
            ...     print(f"Inliers: {result.num_inliers}/{len(matches)}")
            ...     print(f"Inlier ratio: {result.inlier_ratio:.2%}")
            ...     print(f"Iterations: {result.iterations}")
            ... else:
            ...     print("Essential matrix estimation failed")

        Note:
            - Requires at least 5 point correspondences for the 5-point algorithm
            - More correspondences generally lead to better and more stable results
            - The quality of matches significantly affects estimation accuracy
            - Camera calibration accuracy directly impacts pose estimation quality
        """
        pass

    @abstractmethod
    def get_min_samples(self) -> int:
        """
        Get the minimum number of samples required for model estimation.

        Returns the minimum number of point correspondences needed to
        estimate an essential matrix. This depends on the specific algorithm
        used for essential matrix computation.

        Common values:
        - 5 points: 5-point algorithm (most common, numerically stable)
        - 8 points: 8-point algorithm (classical, requires more points)

        Returns:
            int: Minimum number of point correspondences required.
                 Typically 5 for the 5-point algorithm or 8 for the 8-point algorithm.

        Example:
            >>> min_samples = estimator.get_min_samples()
            >>> print(f"Need at least {min_samples} correspondences")
            >>> if len(matches) < min_samples:
            ...     raise ValueError("Insufficient correspondences for estimation")

        Note:
            The 5-point algorithm is generally preferred as it:
            - Requires fewer correspondences
            - Is more numerically stable
            - Handles degenerate configurations better
            - Is less sensitive to noise
        """
        pass

    def validate_inputs(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
        K: np.ndarray,
    ) -> None:
        """
        Validate input parameters for essential matrix estimation.

        Performs comprehensive validation of all input parameters to ensure
        they meet the requirements for robust essential matrix estimation.

        Args:
            keypoints1: Keypoints from first image
            keypoints2: Keypoints from second image
            matches: Point correspondences
            K: Camera intrinsic matrix

        Raises:
            ValidationError: If any input parameter is invalid

        Validation Checks:
        - Sufficient number of correspondences
        - Valid camera matrix format and values
        - Consistent keypoint and match dimensions
        - Reasonable coordinate ranges
        """
        # Validate minimum correspondences
        min_samples = self.get_min_samples()
        match_pairs = matches.matches if hasattr(matches, "matches") else []
        if len(match_pairs) < min_samples:
            raise ValueError(
                f"Insufficient correspondences: need at least {min_samples}, "
                f"got {len(match_pairs)}"
            )

        # Validate camera matrix
        if K.shape != (3, 3):
            raise ValueError(f"Camera matrix must be 3x3, got shape {K.shape}")

        if not np.allclose(K[2, :], [0, 0, 1]):
            raise ValueError("Camera matrix must have [0, 0, 1] as last row")

        # Validate keypoint consistency
        max_idx1 = max(i for i, _ in match_pairs) if match_pairs else -1
        max_idx2 = max(j for _, j in match_pairs) if match_pairs else -1

        if max_idx1 >= len(keypoints1):
            raise ValueError("Match indices exceed keypoints1 length")

        if max_idx2 >= len(keypoints2):
            raise ValueError("Match indices exceed keypoints2 length")
