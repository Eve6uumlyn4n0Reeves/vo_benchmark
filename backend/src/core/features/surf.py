# SURF feature extractor implementation (requires opencv-contrib-python)
from typing import Dict, Any, List
import numpy as np
import cv2
import logging
from src.core.features.base import FeatureExtractor
from src.models.frame import FrameFeatures
from src.models.types import Point2D

logger = logging.getLogger(__name__)


class SURFExtractor(FeatureExtractor):
    """SURF feature extractor (float descriptors). For research/non-commercial use."""

    def __init__(self, config: Dict[str, Any]):
        default_config = {
            "hessianThreshold": 400,
            "nOctaves": 4,
            "nOctaveLayers": 3,
            "extended": False,  # 128-d if True; 64-d if False
            "upright": False,
        }
        final_config = {**default_config, **(config or {})}
        self.config = final_config
        try:
            self.surf = cv2.xfeatures2d.SURF_create(**final_config)  # type: ignore[attr-defined]
            logger.info(f"Initialized SURF with config: {final_config}")
        except Exception as e:
            logger.error("SURF not available. Ensure opencv-contrib-python is installed. %s", e)
            raise

    def extract(self, image: np.ndarray) -> FrameFeatures:
        if image is None or image.size == 0:
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        if gray.dtype != np.uint8:
            gray = (gray * 255).astype(np.uint8) if gray.max() <= 1.0 else gray.astype(np.uint8)
        kps, desc = self.surf.detectAndCompute(gray, None)
        if not kps:
            return FrameFeatures(keypoints=[], descriptors=None, scores=None)
        kp_coords: List[Point2D] = [(kp.pt[0], kp.pt[1]) for kp in kps]
        scores = [kp.response for kp in kps]
        return FrameFeatures(keypoints=kp_coords, descriptors=desc, scores=scores)

    def get_descriptor_size(self) -> int:
        return 128 if self.config.get("extended", False) else 64

    def get_descriptor_type(self) -> np.dtype[Any]:
        return np.dtype(np.float32)

