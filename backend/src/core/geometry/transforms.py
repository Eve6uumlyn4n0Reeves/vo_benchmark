#
# 功能: 定义更复杂的几何变换和验证函数。
#
import numpy as np
from typing import Tuple
from .pose import decompose_pose, create_pose


def essential_matrix_to_pose(
    E: np.ndarray, K: np.ndarray, points1: np.ndarray, points2: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    # 使用OpenCV的recoverPose函数
    import cv2

    _, R, t, _ = cv2.recoverPose(E, points1, points2, K)
    return R, t


def fundamental_matrix_to_essential_matrix(F: np.ndarray, K: np.ndarray) -> np.ndarray:
    return K.T @ F @ K


def is_valid_rotation_matrix(R: np.ndarray, tol: float = 1e-6) -> bool:
    if R.shape != (3, 3):
        return False
    should_be_identity = R @ R.T
    if not np.allclose(should_be_identity, np.eye(3), atol=tol):
        return False
    if not np.isclose(np.linalg.det(R), 1.0, atol=tol):
        return False
    return True


def is_valid_pose(pose: np.ndarray, tol: float = 1e-6) -> bool:
    if pose.shape != (4, 4):
        return False
    if not np.allclose(pose[3, :], [0, 0, 0, 1], atol=tol):
        return False
    return is_valid_rotation_matrix(pose[:3, :3], tol)


# Additional transform functions to satisfy imports
def rotation_matrix_from_euler(angles: np.ndarray, order: str = "xyz") -> np.ndarray:
    """Create rotation matrix from Euler angles"""
    from scipy.spatial.transform import Rotation as R

    r = R.from_euler(order, angles)
    return r.as_matrix()


def rotation_matrix_from_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
    """Create rotation matrix from axis-angle representation"""
    from scipy.spatial.transform import Rotation as R

    r = R.from_rotvec(axis * angle)
    return r.as_matrix()


def rotation_matrix_from_quaternion(q: np.ndarray) -> np.ndarray:
    """Create rotation matrix from quaternion [w, x, y, z]"""
    from scipy.spatial.transform import Rotation as R

    # Convert from [w,x,y,z] to scipy format [x,y,z,w]
    q_scipy = [q[1], q[2], q[3], q[0]]
    r = R.from_quat(q_scipy)
    return r.as_matrix()


def quaternion_from_rotation_matrix(R: np.ndarray) -> np.ndarray:
    """Extract quaternion [w, x, y, z] from rotation matrix"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_matrix(R)
    q_scipy = r.as_quat()  # [x,y,z,w]
    return np.array([q_scipy[3], q_scipy[0], q_scipy[1], q_scipy[2]])  # [w,x,y,z]


def euler_from_rotation_matrix(R: np.ndarray, order: str = "xyz") -> np.ndarray:
    """Extract Euler angles from rotation matrix"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_matrix(R)
    from typing import cast, Literal
    return r.as_euler(cast(Literal['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx'], order))


def axis_angle_from_rotation_matrix(R: np.ndarray) -> Tuple[np.ndarray, float]:
    """Extract axis-angle representation from rotation matrix"""
    from scipy.spatial.transform import Rotation as R_scipy

    r = R_scipy.from_matrix(R)
    rotvec = r.as_rotvec()
    angle = np.linalg.norm(rotvec)
    if angle > 1e-8:
        axis = rotvec / angle
    else:
        axis = np.array([1, 0, 0])  # Default axis for zero rotation
    return axis, float(angle)


def pose_matrix(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Create 4x4 pose matrix from rotation and translation"""
    pose = np.eye(4)
    pose[:3, :3] = R
    pose[:3, 3] = t.flatten()
    return pose


def decompose_pose_matrix(pose: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Decompose 4x4 pose matrix into rotation and translation"""
    return pose[:3, :3], pose[:3, 3].reshape(3, 1)


def invert_pose_matrix(pose: np.ndarray) -> np.ndarray:
    """Invert a 4x4 pose matrix"""
    R, t = decompose_pose_matrix(pose)
    R_inv = R.T
    t_inv = -R_inv @ t
    return pose_matrix(R_inv, t_inv)


def compose_poses(pose1: np.ndarray, pose2: np.ndarray) -> np.ndarray:
    """Compose two pose matrices"""
    return pose1 @ pose2


def relative_pose(pose1: np.ndarray, pose2: np.ndarray) -> np.ndarray:
    """Compute relative pose from pose1 to pose2"""
    return invert_pose_matrix(pose1) @ pose2


def transform_points_3d(points: np.ndarray, pose: np.ndarray) -> np.ndarray:
    """Transform 3D points using pose matrix"""
    if points.shape[1] == 3:
        points_h = np.hstack([points, np.ones((points.shape[0], 1))])
    else:
        points_h = points
    transformed_h = (pose @ points_h.T).T
    return transformed_h[:, :3]


def transform_points_2d(points: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Transform 2D points using homography matrix"""
    if points.shape[1] == 2:
        points_h = np.hstack([points, np.ones((points.shape[0], 1))])
    else:
        points_h = points
    transformed_h = (H @ points_h.T).T
    # Normalize homogeneous coordinates
    transformed_h = transformed_h / transformed_h[:, 2:3]
    return transformed_h[:, :2]


def essential_matrix_to_pose_compat(
    E: np.ndarray, K: np.ndarray, points1: np.ndarray, points2: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Recover pose from essential matrix (alias for compatibility)"""
    import cv2

    _, R, t, _ = cv2.recoverPose(E, points1, points2, K)
    return R, t


def fundamental_matrix_to_essential(F: np.ndarray, K: np.ndarray) -> np.ndarray:
    """Convert fundamental matrix to essential matrix (alias)"""
    return fundamental_matrix_to_essential_matrix(F, K)


def essential_matrix_from_pose(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Create essential matrix from pose"""
    t_skew = skew_symmetric_matrix(t.flatten())
    return t_skew @ R


def skew_symmetric_matrix(v: np.ndarray) -> np.ndarray:
    """Create skew-symmetric matrix from 3D vector"""
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def normalize_rotation_matrix(R: np.ndarray) -> np.ndarray:
    """Normalize rotation matrix using SVD"""
    U, _, Vt = np.linalg.svd(R)
    R_normalized = U @ Vt
    # Ensure proper rotation (det = 1, not -1)
    if np.linalg.det(R_normalized) < 0:
        Vt[-1, :] *= -1
        R_normalized = U @ Vt
    return R_normalized


def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute angle between two vectors in radians"""
    v1_norm = v1 / np.linalg.norm(v1)
    v2_norm = v2 / np.linalg.norm(v2)
    cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    return np.arccos(cos_angle)


def interpolate_poses(pose1: np.ndarray, pose2: np.ndarray, t: float) -> np.ndarray:
    """Interpolate between two poses using SLERP for rotation and linear for translation"""
    from scipy.spatial.transform import Rotation as R, Slerp

    # Extract rotations and translations
    R1, t1 = decompose_pose_matrix(pose1)
    R2, t2 = decompose_pose_matrix(pose2)

    # Interpolate rotation using SLERP
    r1 = R.from_matrix(R1)
    r2 = R.from_matrix(R2)
    slerp = Slerp([0, 1], R.concatenate([r1, r2]))
    R_interp = slerp(np.array([t])).as_matrix()

    # Linear interpolation for translation
    t_interp = (1 - t) * t1.flatten() + t * t2.flatten()

    return pose_matrix(R_interp, t_interp)


def pose_distance(pose1: np.ndarray, pose2: np.ndarray) -> Tuple[float, float]:
    """Compute translation and rotation distance between poses"""
    R1, t1 = decompose_pose_matrix(pose1)
    R2, t2 = decompose_pose_matrix(pose2)

    # Translation distance
    trans_dist = np.linalg.norm(t1.flatten() - t2.flatten())

    # Rotation distance
    R_rel = R1.T @ R2
    trace = np.trace(R_rel)
    rot_dist_rad = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))

    return float(trans_dist), float(np.degrees(rot_dist_rad))


def validate_rotation_matrix(R: np.ndarray, tolerance: float = 1e-6) -> bool:
    """Validate rotation matrix (alias for is_valid_rotation_matrix)"""
    return is_valid_rotation_matrix(R, tolerance)


def validate_pose_matrix(pose: np.ndarray, tolerance: float = 1e-6) -> bool:
    """Validate pose matrix (alias for is_valid_pose)"""
    return is_valid_pose(pose, tolerance)
