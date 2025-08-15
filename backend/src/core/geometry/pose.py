#
# 功能: 定义位姿和几何变换函数。
#
from typing import List, Optional, Tuple
import numpy as np
from src.models.types import Pose, Rotation, Translation


def identity_pose() -> Pose:
    return np.eye(4)


def create_pose(rotation: Rotation, translation: Translation) -> Pose:
    pose = np.eye(4)
    pose[:3, :3] = rotation
    pose[:3, 3] = translation.flatten()
    return pose


def decompose_pose(pose: Pose) -> Tuple[Rotation, Translation]:
    return pose[:3, :3], pose[:3, 3].reshape(3, 1)


def invert_pose(pose: Pose) -> Pose:
    R, t = decompose_pose(pose)
    R_inv = R.T
    t_inv = -R_inv @ t
    return create_pose(R_inv, t_inv)


def compose_poses(pose1: Pose, pose2: Pose) -> Pose:
    return pose1 @ pose2


def transform_points(points: np.ndarray, pose: Pose) -> np.ndarray:
    points_h = np.hstack([points, np.ones((points.shape[0], 1))])
    transformed_h = (pose @ points_h.T).T
    return transformed_h[:, :3]


def pose_distance(pose1: Pose, pose2: Pose) -> Tuple[float, float]:
    t1, t2 = pose1[:3, 3], pose2[:3, 3]
    trans_dist = np.linalg.norm(t1 - t2)

    R1, R2 = pose1[:3, :3], pose2[:3, :3]
    R_rel = R1.T @ R2
    trace = np.trace(R_rel)
    rot_dist_rad = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))
    return float(trans_dist), float(np.degrees(rot_dist_rad))


def rodrigues_to_rotation_matrix(rvec: np.ndarray) -> Rotation:
    """Convert Rodrigues vector to rotation matrix using OpenCV"""
    import cv2

    R, _ = cv2.Rodrigues(rvec)
    return R


def rotation_matrix_to_rodrigues(R: Rotation) -> np.ndarray:
    """Convert rotation matrix to Rodrigues vector using OpenCV"""
    import cv2

    rvec, _ = cv2.Rodrigues(R)
    return rvec.flatten()


def euler_to_rotation_matrix(angles: np.ndarray, order: str = "xyz") -> Rotation:
    """Convert Euler angles to rotation matrix"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_euler(order, angles)
    return r.as_matrix()


def rotation_matrix_to_euler(R: Rotation, order: str = "xyz") -> np.ndarray:
    """Convert rotation matrix to Euler angles"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_matrix(R)
    from typing import cast, Literal
    return r.as_euler(cast(Literal['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx'], order))


def quaternion_to_rotation_matrix(q: np.ndarray) -> Rotation:
    """Convert quaternion [w, x, y, z] to rotation matrix"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_quat([q[1], q[2], q[3], q[0]])  # scipy uses [x,y,z,w]
    return r.as_matrix()


def rotation_matrix_to_quaternion(R: Rotation) -> np.ndarray:
    """Convert rotation matrix to quaternion [w, x, y, z]"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_matrix(R)
    q_scipy = r.as_quat()  # returns [x,y,z,w]
    return np.array([q_scipy[3], q_scipy[0], q_scipy[1], q_scipy[2]])  # [w,x,y,z]


def essential_matrix_to_pose(
    E: np.ndarray, K: np.ndarray, points1: np.ndarray, points2: np.ndarray
) -> Tuple[Rotation, Translation]:
    """Recover pose from essential matrix"""
    import cv2

    # Decompose essential matrix
    R1, R2, t = cv2.decomposeEssentialMat(E)

    # Test all four possible combinations
    poses = [(R1, t), (R1, -t), (R2, t), (R2, -t)]
    best_pose = None
    max_inliers = 0

    for R, t_vec in poses:
        # Check cheirality (points in front of both cameras)
        inliers = 0
        for i in range(min(10, len(points1))):  # Test subset for efficiency
            # Triangulate point
            P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
            P2 = K @ np.hstack([R, t_vec.reshape(3, 1)])

            # Convert boolean mask to float for triangulatePoints
            p1_float = points1[i : i + 1].T.astype(np.float64)
            p2_float = points2[i : i + 1].T.astype(np.float64)
            point_4d = cv2.triangulatePoints(P1.astype(np.float64), P2.astype(np.float64), p1_float, p2_float)
            point_3d = point_4d[:3] / point_4d[3]

            # Check if point is in front of both cameras
            if point_3d[2] > 0 and (R @ point_3d + t_vec.reshape(3, 1))[2] > 0:
                inliers += 1

        if inliers > max_inliers:
            max_inliers = inliers
            best_pose = (R, t_vec.reshape(3, 1))

    return best_pose if best_pose else (R1, t.reshape(3, 1))


def fundamental_matrix_to_essential_matrix(F: np.ndarray, K: np.ndarray) -> np.ndarray:
    """Convert fundamental matrix to essential matrix"""
    return K.T @ F @ K


def is_valid_rotation_matrix(R: np.ndarray, tolerance: float = 1e-6) -> bool:
    """Check if matrix is a valid rotation matrix"""
    if R.shape != (3, 3):
        return False

    # Check orthogonality: R @ R.T should be identity
    should_be_identity = R @ R.T
    identity = np.eye(3)
    if not np.allclose(should_be_identity, identity, atol=tolerance):
        return False

    # Check determinant should be 1 (not -1 for reflection)
    det = np.linalg.det(R)
    if not np.isclose(det, 1.0, atol=tolerance):
        return False

    return True


def is_valid_pose(pose: Pose, tolerance: float = 1e-6) -> bool:
    """Check if matrix is a valid pose matrix"""
    if pose.shape != (4, 4):
        return False

    # Check rotation part
    R = pose[:3, :3]
    if not is_valid_rotation_matrix(R, tolerance):
        return False

    # Check bottom row should be [0, 0, 0, 1]
    expected_bottom = np.array([0, 0, 0, 1])
    if not np.allclose(pose[3, :], expected_bottom, atol=tolerance):
        return False

    return True
