# Documentation Standards Guide

## Overview

This document establishes comprehensive documentation standards for the VO-Benchmark project to ensure consistency, maintainability, and clarity across all code components.

## General Principles

### 1. Language Standards
- **Primary Language**: All documentation must be written in English
- **Consistency**: Use consistent terminology throughout the project
- **Clarity**: Write clear, concise documentation that explains both "what" and "why"
- **Audience**: Write for developers who are new to the codebase

### 2. Documentation Types
- **Code Comments**: Inline explanations for complex logic
- **API Documentation**: Comprehensive endpoint documentation
- **Type Documentation**: Interface and type definitions
- **Module Documentation**: High-level component explanations

## TypeScript/Frontend Documentation Standards

### 1. File Headers
Every TypeScript file should start with a comprehensive file header:

```typescript
/**
 * @fileoverview Brief description of the file's purpose
 * 
 * Detailed description explaining the component's role in the system,
 * key algorithms used, and important implementation details.
 * 
 * @author VO-Benchmark Team
 * @version 1.0.0
 * @since 2024-01-01
 */
```

### 2. Interface Documentation
All interfaces must include JSDoc comments:

```typescript
/**
 * Represents configuration options for feature extraction
 */
interface FeatureConfig {
  /** Maximum number of features to extract (default: 5000) */
  maxFeatures: number;
  /** Contrast threshold for feature detection (0.01-0.1) */
  contrastThreshold: number;
  /** Edge threshold to filter weak edges (1-20) */
  edgeThreshold: number;
}
```

### 3. Function Documentation
All functions must include comprehensive JSDoc:

```typescript
/**
 * Extracts SIFT features from an input image
 * 
 * This function applies the Scale-Invariant Feature Transform algorithm
 * to detect and describe local features in the image. The algorithm is
 * particularly robust to scale and rotation changes.
 * 
 * @param image - Input image as ImageData or HTMLImageElement
 * @param config - Configuration options for feature extraction
 * @returns Promise resolving to extracted features and descriptors
 * 
 * @throws {FeatureExtractionError} When image processing fails
 * @throws {ValidationError} When config parameters are invalid
 * 
 * @example
 * ```typescript
 * const features = await extractSIFTFeatures(imageData, {
 *   maxFeatures: 1000,
 *   contrastThreshold: 0.04,
 *   edgeThreshold: 10
 * });
 * console.log(`Extracted ${features.keypoints.length} features`);
 * ```
 */
async function extractSIFTFeatures(
  image: ImageData | HTMLImageElement,
  config: FeatureConfig
): Promise<FeatureResult> {
  // Implementation...
}
```

### 4. Component Documentation
React components require detailed documentation:

```typescript
/**
 * ExperimentDashboard Component
 * 
 * Displays a comprehensive dashboard for monitoring experiment progress,
 * including real-time status updates, performance metrics, and result
 * visualizations. Supports both active and completed experiments.
 * 
 * @param props - Component props
 * @returns JSX element containing the dashboard interface
 * 
 * @example
 * ```tsx
 * <ExperimentDashboard
 *   experimentId="exp_001"
 *   refreshInterval={5000}
 *   showDetailedMetrics={true}
 * />
 * ```
 */
export function ExperimentDashboard(props: ExperimentDashboardProps) {
  // Component implementation...
}
```

## Python/Backend Documentation Standards

### 1. Module Docstrings
Every Python module should start with a comprehensive docstring:

```python
"""
Feature Extraction Module

This module provides implementations of various feature extraction algorithms
for visual odometry applications, including SIFT, ORB, and custom descriptors.
All extractors follow a common interface defined in the base class.

The module supports:
- Multiple feature types with configurable parameters
- Batch processing for improved performance
- Caching mechanisms for repeated extractions
- Error handling and validation

Example:
    Basic usage of the SIFT extractor:
    
    >>> from core.features import SIFTExtractor
    >>> extractor = SIFTExtractor({'max_features': 1000})
    >>> features = extractor.extract(image)
    >>> print(f"Extracted {len(features.keypoints)} keypoints")

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""
```

### 2. Class Documentation
All classes must include comprehensive docstrings:

```python
class SIFTExtractor(FeatureExtractor):
    """
    Scale-Invariant Feature Transform (SIFT) feature extractor.
    
    This class implements the SIFT algorithm for detecting and describing
    local features in images. SIFT features are invariant to scale, rotation,
    and partially invariant to illumination changes and affine transformations.
    
    The implementation uses OpenCV's SIFT detector with configurable parameters
    for different use cases and performance requirements.
    
    Attributes:
        config (Dict[str, Any]): Configuration parameters for the extractor
        detector (cv2.SIFT): OpenCV SIFT detector instance
        
    Example:
        >>> extractor = SIFTExtractor({
        ...     'max_features': 5000,
        ...     'contrast_threshold': 0.04,
        ...     'edge_threshold': 10
        ... })
        >>> features = extractor.extract(image)
        
    Note:
        SIFT is patented and may require licensing for commercial use.
        Consider using ORB for patent-free alternatives.
    """
```

### 3. Function Documentation
All functions must follow Google-style docstrings:

```python
def estimate_essential_matrix(
    keypoints1: List[Point2D],
    keypoints2: List[Point2D], 
    matches: FrameMatches,
    camera_matrix: np.ndarray,
    ransac_config: Dict[str, Any]
) -> RANSACResult:
    """
    Estimates essential matrix using RANSAC from matched keypoints.
    
    This function implements the 5-point algorithm within a RANSAC framework
    to robustly estimate the essential matrix from noisy point correspondences.
    The essential matrix encodes the epipolar geometry between two camera views.
    
    Args:
        keypoints1: Keypoints from the first image as (x, y) coordinates
        keypoints2: Keypoints from the second image as (x, y) coordinates  
        matches: Validated matches between keypoints with confidence scores
        camera_matrix: 3x3 camera intrinsic matrix [fx, 0, cx; 0, fy, cy; 0, 0, 1]
        ransac_config: RANSAC parameters including:
            - threshold: Inlier threshold in pixels (default: 1.0)
            - confidence: Desired confidence level (default: 0.999)
            - max_iters: Maximum RANSAC iterations (default: 2000)
            
    Returns:
        RANSACResult containing:
            - essential_matrix: 3x3 essential matrix
            - inlier_mask: Boolean mask indicating inlier correspondences
            - num_inliers: Number of inlier correspondences
            - iterations: Actual RANSAC iterations performed
            - success: Whether estimation succeeded
            
    Raises:
        RANSACError: When insufficient matches or estimation fails
        ValidationError: When input parameters are invalid
        
    Example:
        >>> result = estimate_essential_matrix(
        ...     kpts1, kpts2, matches, K, 
        ...     {'threshold': 1.0, 'confidence': 0.999}
        ... )
        >>> if result.success:
        ...     print(f"Found {result.num_inliers} inliers")
        
    Note:
        Requires at least 5 point correspondences for the 5-point algorithm.
        More correspondences generally lead to better results.
    """
```

## API Documentation Standards

### 1. OpenAPI/Swagger Integration
All REST endpoints must be documented using OpenAPI specifications:

```python
from flask_restx import Api, Resource, fields

# API namespace definition
experiments_ns = api.namespace('experiments', description='Experiment management operations')

# Request/Response models
experiment_model = api.model('Experiment', {
    'name': fields.String(required=True, description='Experiment name', example='sift_vs_orb_comparison'),
    'dataset_path': fields.String(required=True, description='Path to dataset directory'),
    'feature_types': fields.List(fields.String, required=True, description='Feature extraction algorithms to test'),
    'ransac_types': fields.List(fields.String, required=True, description='RANSAC variants to evaluate'),
    'sequences': fields.List(fields.String, description='Dataset sequences to process'),
    'num_runs': fields.Integer(default=1, description='Number of runs per algorithm combination')
})

@experiments_ns.route('/')
class ExperimentList(Resource):
    @experiments_ns.doc('create_experiment')
    @experiments_ns.expect(experiment_model)
    @experiments_ns.marshal_with(experiment_response_model, code=201)
    @experiments_ns.response(400, 'Validation Error')
    @experiments_ns.response(500, 'Internal Server Error')
    def post(self):
        """
        Create a new experiment
        
        Creates and initializes a new experiment with the specified configuration.
        The experiment will be queued for execution and can be monitored via
        the tasks endpoint.
        """
        # Implementation...
```

## Configuration Documentation

### 1. Parameter Documentation
All configuration parameters must be thoroughly documented:

```python
class ExperimentConfig(BaseModel):
    """
    Configuration model for experiment execution.
    
    This model defines all parameters needed to configure and run
    a feature matching experiment, including algorithm selection,
    dataset specification, and output options.
    """
    
    name: str = Field(
        ..., 
        description="Human-readable experiment name",
        example="sift_orb_comparison_tum_rgbd",
        min_length=1,
        max_length=100
    )
    
    dataset_path: Path = Field(
        ...,
        description="Absolute path to dataset root directory. Must contain valid TUM or KITTI format data.",
        example="/data/datasets/TUM_RGBD/rgbd_dataset_freiburg1_xyz"
    )
    
    feature_types: List[FeatureType] = Field(
        ...,
        description="List of feature extraction algorithms to evaluate. Supported: SIFT, ORB",
        example=["SIFT", "ORB"],
        min_items=1
    )
    
    max_features: int = Field(
        default=5000,
        description="Maximum number of features to extract per image. Higher values increase accuracy but reduce speed.",
        ge=100,
        le=20000,
        example=5000
    )
```

## Inline Comments Standards

### 1. Complex Algorithm Explanations
```python
def prosac_estimation(matches, threshold, confidence):
    """PROSAC (Progressive Sample Consensus) implementation."""
    
    # Sort matches by quality score (PROSAC requirement)
    # Higher quality matches are sampled first to improve convergence
    sorted_matches = sorted(matches, key=lambda m: m.confidence, reverse=True)
    
    # Progressive sampling: start with highest quality matches
    # and gradually include lower quality ones
    for n in range(MIN_SAMPLES, len(sorted_matches)):
        subset = sorted_matches[:n]
        
        # Calculate sampling probability based on match quality
        # P(i) = quality_i / sum(quality_j for j in subset)
        probabilities = [m.confidence for m in subset]
        probabilities = np.array(probabilities) / np.sum(probabilities)
        
        # Sample minimal set using quality-weighted selection
        sample_indices = np.random.choice(n, MIN_SAMPLES, p=probabilities)
        sample_matches = [subset[i] for i in sample_indices]
        
        # Estimate model and evaluate
        model = estimate_model(sample_matches)
        inliers = evaluate_model(model, subset, threshold)
        
        # Early termination if sufficient inliers found
        if len(inliers) >= min_inliers_for_confidence(confidence):
            return model, inliers
```

### 2. Performance-Critical Sections
```typescript
// Optimized feature matching using spatial indexing
// This implementation uses a k-d tree for O(log n) nearest neighbor search
// instead of brute force O(n²) comparison, significantly improving performance
// for large feature sets (>1000 features)
const spatialIndex = new KDTree(descriptors1, euclideanDistance);

// Batch process matches to leverage CPU cache efficiency
// Process in chunks of 64 to optimize memory access patterns
const BATCH_SIZE = 64;
for (let i = 0; i < descriptors2.length; i += BATCH_SIZE) {
  const batch = descriptors2.slice(i, i + BATCH_SIZE);
  const batchMatches = batch.map(desc => spatialIndex.nearest(desc, 2));
  matches.push(...batchMatches);
}
```

## Documentation Maintenance

### 1. Version Control
- Update documentation with every code change
- Include documentation updates in pull requests
- Use semantic versioning for API changes

### 2. Review Process
- All documentation changes require peer review
- Validate examples and code snippets
- Ensure consistency with existing documentation

### 3. Automated Checks
- Use linters to enforce documentation standards
- Generate documentation from code comments
- Validate API documentation against implementation

## Tools and Integration

### 1. TypeScript
- Use TSDoc for comprehensive type documentation
- Enable strict type checking
- Generate API documentation from types

### 2. Python
- Use Sphinx for documentation generation
- Follow Google or NumPy docstring conventions
- Integrate with type hints

### 3. API Documentation
- Use Flask-RESTX for OpenAPI generation
- Provide interactive API explorer
- Include request/response examples

This standards guide ensures consistent, high-quality documentation across the entire VO-Benchmark project.
