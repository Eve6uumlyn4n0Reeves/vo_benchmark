# BRISK feature extractor implementation
from typing import Dict, Any, List
import numpy as np
import cv2
import logging
from src.core.features.base import FeatureExtractor
from src.models.frame import FrameFeatures
from src.models.types import Point2D

logger = logging.getLogger(__name__)


class BRISKExtractor(FeatureExtractor):
    """BRISK feature extractor (binary descriptor)."""

    def __init__(self, config: Dict[str, Any]):
        default_config = {
            # cv2.BRISK_create params
            "thresh": 30,
            "octaves": 3,
            "patternScale": 1.0,
        }
        final_config = {**default_config, **(config or {})}
        self.config = final_config
        try:
            from typing import cast, Any
            self.brisk = cast(Any, cv2).BRISK_create(**final_config)
            logger.info(f"Initialized BRISK with config: {final_config}")
        except Exception as e:
            logger.error(f"Failed to initialize BRISK: {e}")
            raise

    def extract(self, image: np.ndarray) -> FrameFeatures:
        if image is None or image.size == 0:
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        if gray.dtype != np.uint8:
            gray = (gray * 255).astype(np.uint8) if gray.max() <= 1.0 else gray.astype(np.uint8)
        kps, desc = self.brisk.detectAndCompute(gray, None)
        if not kps:
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)
        kp_coords: List[Point2D] = [(kp.pt[0], kp.pt[1]) for kp in kps]
        scores = [kp.response for kp in kps]
        return FrameFeatures(keypoints=kp_coords, descriptors=desc, scores=scores)

    def get_descriptor_size(self) -> int:
        return 64  # BRISK default length (bytes)

    def get_descriptor_type(self) -> np.dtype[Any]:
        return np.dtype(np.uint8)

