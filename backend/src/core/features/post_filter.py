# Post-matching filters (GMS and fallbacks)
from typing import List, Tuple
import logging
import numpy as np
import cv2
from src.models.frame import FrameMatches

logger = logging.getLogger(__name__)


# Cache GMS capability detection to avoid repeated attempts/log spam
_GMS_CHECKED: bool = False
_GMS_AVAILABLE: bool = False
_GMS_LOGGED: bool = False


def _check_gms_available() -> bool:
    global _GMS_CHECKED, _GMS_AVAILABLE, _GMS_LOGGED
    if _GMS_CHECKED:
        return _GMS_AVAILABLE
    try:
        import cv2  # local to be safe with lazy importers
        _GMS_AVAILABLE = hasattr(cv2, "xfeatures2d") and hasattr(cv2.xfeatures2d, "matchGMS")  # type: ignore[attr-defined]
    except Exception:
        _GMS_AVAILABLE = False
    _GMS_CHECKED = True
    if not _GMS_LOGGED and not _GMS_AVAILABLE:
        # Only log once to avoid console flooding
        logger.info("OpenCV GMS (xfeatures2d.matchGMS) not available; using symmetric+MAD filter.")
        _GMS_LOGGED = True
    return _GMS_AVAILABLE

MatchPair = Tuple[int, int]


def _to_keypoints(points: List[Tuple[float, float]]):
    """Convert (x, y) list to cv2.KeyPoint list."""
    return [cv2.KeyPoint(x=float(x), y=float(y), size=1) for (x, y) in points]


def _to_dmatches(pairs: List[MatchPair]):
    """Convert match index pairs to cv2.DMatch list (distance=0 as placeholder)."""
    return [cv2.DMatch(_queryIdx=i, _trainIdx=j, _imgIdx=0, _distance=0) for (i, j) in pairs]


def _pairs_from_dmatches(matches: List[cv2.DMatch]) -> List[MatchPair]:
    return [(int(m.queryIdx), int(m.trainIdx)) for m in matches]


def apply_gms_filter(
    image_shape1: Tuple[int, int],
    image_shape2: Tuple[int, int],
    keypoints1: List[Tuple[float, float]],
    keypoints2: List[Tuple[float, float]],
    matches: FrameMatches,
    with_rotation: bool = False,
    with_scale: bool = False,
    threshold_factor: int = 6,
) -> FrameMatches:
    """
    Try to apply OpenCV's GMS (Grid-based Motion Statistics) filter to matches.
    If xfeatures2d.matchGMS is unavailable, fall back to a robust symmetric + MAD filter.
    image_shape: (H, W)
    """
    try:
        # Try OpenCV contrib implementation (once)
        if not _check_gms_available():
            raise RuntimeError("OpenCV GMS not available")
        kp1 = _to_keypoints(keypoints1)
        kp2 = _to_keypoints(keypoints2)
        dm = _to_dmatches(matches.matches)
        inlier_matches = cv2.xfeatures2d.matchGMS(  # type: ignore[attr-defined]
            (int(image_shape1[1]), int(image_shape1[0])),
            (int(image_shape2[1]), int(image_shape2[0])),
            kp1,
            kp2,
            dm,
            with_rotation,
            with_scale,
            threshold_factor,
        )
        # matchGMS may return a list of DMatch or mask indices depending on version
        if isinstance(inlier_matches, (list, tuple)) and len(inlier_matches) > 0:
            if isinstance(inlier_matches[0], cv2.DMatch):
                from typing import cast, List
                from cv2 import DMatch
                filtered_pairs = _pairs_from_dmatches(cast(List[DMatch], inlier_matches))
            else:
                # Assume indices of inliers
                filtered_pairs = [matches.matches[int(i)] for i in inlier_matches]
        else:
            filtered_pairs = matches.matches
        # Preserve scores for kept matches
        keep = set(filtered_pairs)
        filtered_scores = [s for (p, s) in zip(matches.matches, matches.scores) if p in keep]
        return FrameMatches(matches=filtered_pairs, scores=filtered_scores)
    except Exception as e:
        # Only warn once to prevent log flooding in long sequences
        global _GMS_LOGGED
        if not _GMS_LOGGED:
            logger.warning(f"GMS not available or failed: {e}. Falling back to symmetric+MAD filter.")
            _GMS_LOGGED = True
        return apply_symmetric_mad_filter(keypoints1, keypoints2, matches)


def apply_symmetric_mad_filter(
    keypoints1: List[Tuple[float, float]],
    keypoints2: List[Tuple[float, float]],
    matches: FrameMatches,
    mad_k: float = 3.0,
) -> FrameMatches:
    """
    Fallback: symmetric consistency check + robust (MAD-based) distance filter.
    Since we don't have distances for symmetry in this abstraction, we perform a simple
    mutual nearest check in index space approximation using a reverse map, then MAD on stored scores.
    """
    try:
        # Build reverse map (train->query) approximate symmetry (based on first unique mapping)
        reverse_map = {}
        for (q, t) in matches.matches:
            if t not in reverse_map:
                reverse_map[t] = q
        symmetric_pairs: List[MatchPair] = []
        for (q, t) in matches.matches:
            if reverse_map.get(t, None) == q:
                symmetric_pairs.append((q, t))
        if not symmetric_pairs:
            symmetric_pairs = matches.matches
        # MAD filter on inverse score (since score ~ 1/(1+d))
        scores = [s for (p, s) in zip(matches.matches, matches.scores) if p in set(symmetric_pairs)]
        pairs = [p for p in symmetric_pairs]
        if not scores:
            return FrameMatches(matches=pairs, scores=[1.0 for _ in pairs])
        inv = np.array([1.0 / max(s, 1e-6) - 1.0 for s in scores], dtype=np.float32)
        med = float(np.median(inv))
        mad = float(np.median(np.abs(inv - med)) + 1e-6)
        upper = med + 1.4826 * mad * mad_k
        filtered = [(p, s) for (p, s, d) in zip(pairs, scores, inv) if d <= upper]
        if not filtered:
            filtered = list(zip(pairs, scores))
        f_pairs = [p for (p, _) in filtered]
        f_scores = [s for (_, s) in filtered]
        return FrameMatches(matches=f_pairs, scores=f_scores)
    except Exception as e:
        logger.error(f"Symmetric MAD filter failed: {e}")
        return matches

