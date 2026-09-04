"""3D view math in patient LPS; independent of QWidget and VTK contexts."""
from dataclasses import dataclass, replace
import math

import numpy as np

from qt_dicom_viewer.model.dicom_core import VolumeGeometry
from qt_dicom_viewer.model.ui_models import DicomSeriesRecord
from qt_dicom_viewer.model.dicom_types import WindowLevel
from qt_dicom_viewer.model.volume_models import VOLUME_DIRECTIONS


# Right=patient left, up=superior, camera on the anterior side.
ANTERIOR_BASIS = np.array(((1, 0, 0), (0, 0, -1), (0, 1, 0)), dtype=float)


@dataclass(frozen=True, slots=True)
class VolumeViewState:
    # Camera-local rotation, w/x/y/z. Pan is measured in viewport heights.
    rotation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    pan: tuple[float, float] = (0.0, 0.0)
    zoom: float = 1.0


def quaternion_product(a, b) -> tuple[float, float, float, float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    result = np.array((aw*bw-ax*bx-ay*by-az*bz,
                       aw*bx+ax*bw+ay*bz-az*by,
                       aw*by-ax*bz+ay*bw+az*bx,
                       aw*bz+ax*by-ay*bx+az*bw))
    result /= np.linalg.norm(result)
    return tuple(float(v) for v in result)


def rotation_matrix(q) -> np.ndarray:
    w, x, y, z = q
    return np.array(((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
                     (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)),
                     (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y))))


def view_basis(state: VolumeViewState) -> np.ndarray:
    return ANTERIOR_BASIS @ rotation_matrix(state.rotation)


def face_rotation(face: str) -> tuple[float, float, float, float]:
    direction = next(d for d in VOLUME_DIRECTIONS if d.face == face)
    back, up = np.asarray(direction.normal), np.asarray(direction.up)
    target = np.column_stack((np.cross(up, back), up, back))
    matrix = ANTERIOR_BASIS.T @ target
    # Symmetric eigenproblem remains stable at 180 degrees (trace=-1).
    m = matrix
    k = np.array((
        (m[0, 0]-m[1, 1]-m[2, 2], m[0, 1]+m[1, 0], m[0, 2]+m[2, 0], m[2, 1]-m[1, 2]),
        (m[0, 1]+m[1, 0], m[1, 1]-m[0, 0]-m[2, 2], m[1, 2]+m[2, 1], m[0, 2]-m[2, 0]),
        (m[0, 2]+m[2, 0], m[1, 2]+m[2, 1], m[2, 2]-m[0, 0]-m[1, 1], m[1, 0]-m[0, 1]),
        (m[2, 1]-m[1, 2], m[0, 2]-m[2, 0], m[1, 0]-m[0, 1], np.trace(m)),
    ))/3
    _, vectors = np.linalg.eigh(k)
    q = vectors[:, -1][[3, 0, 1, 2]]
    if q[0] < 0:
        q = -q
    return tuple(float(v) for v in q)


def nearest_face(state: VolumeViewState, previous="A") -> str:
    back = view_basis(state)[:, 2]
    scores = {d.face: float(np.dot(back, d.normal)) for d in VOLUME_DIRECTIONS}
    best = max(scores.values())
    if scores.get(previous, -1) >= best-1e-6:
        return previous
    return next(face for face, score in scores.items() if score >= best-1e-6)


def drag_volume_window(window: WindowLevel, delta, size) -> WindowLevel:
    # Match the 2D tool's normalized sensitivity, without its inversion gesture.
    control_range = min(1000.0, max(100.0, window.width))
    return WindowLevel(
        center=round(window.center-delta[1]*control_range/max(1, size[1]), 2),
        width=round(max(1.0, window.width+delta[0]*control_range/max(1, size[0])), 2),
    )


def _arcball(point, size):
    width, height = size
    scale = max(1.0, min(width, height))
    x, y = (2*point[0]-width)/scale, (height-2*point[1])/scale
    radius2 = x*x+y*y
    v = np.array((x, y, math.sqrt(max(0.0, 1-radius2))))
    return v / max(1.0, np.linalg.norm(v))


def rotate_drag(state: VolumeViewState, start, end, size) -> VolumeViewState:
    a, b = _arcball(start, size), _arcball(end, size)
    dot = float(np.clip(np.dot(a, b), -1, 1))
    axis = np.cross(a, b)
    if dot < -0.999999:
        axis = np.cross(a, (1, 0, 0) if abs(a[0]) < 0.9 else (0, 1, 0))
        axis /= np.linalg.norm(axis)
        delta = (0.0, *axis)
    else:
        delta = np.array((1+dot, *axis))
        delta /= np.linalg.norm(delta)
    # Rotate the camera inversely so the displayed anatomy follows the pointer.
    inverse = (delta[0], -delta[1], -delta[2], -delta[3])
    return replace(state, rotation=quaternion_product(state.rotation, inverse))


def zoom_by(state: VolumeViewState, exponent: float) -> VolumeViewState:
    value = state.zoom * 2**max(-20.0, min(20.0, exponent))
    return replace(state, zoom=max(0.1, min(20.0, value)))


def camera_parameters(geometry: VolumeGeometry, state: VolumeViewState, size):
    width, height = size
    basis = view_basis(state)
    extent = np.array(((geometry.columns-1)*geometry.column_spacing,
                       (geometry.rows-1)*geometry.row_spacing,
                       (geometry.slice_count-1)*geometry.slice_spacing))
    radius = max(1.0, float(np.linalg.norm(extent))/2)
    aspect = max(1.0, width)/max(1.0, height)
    scale = radius * 1.1 * max(1.0, 1/aspect) / state.zoom
    offset = 2*scale*(-state.pan[0]*basis[:, 0]+state.pan[1]*basis[:, 1])
    focal = np.asarray(geometry.center_patient) + offset
    return dict(position=focal+4*radius*basis[:, 2], focal=focal,
                up=basis[:, 1], scale=scale, clipping=(radius, 7*radius))


def validate_volume_series(series: DicomSeriesRecord) -> None:
    """A 3D texture needs a regular orthogonal grid, not a median-spacing guess."""
    instances = series.instances
    if len(instances) < 2:
        raise ValueError("3D 需要至少两张具有空间位置的切片")
    first = instances[0]
    if first.image_orientation_patient is None or any(
        item.image_position_patient is None for item in instances
    ):
        raise ValueError("3D 缺少切片位置或方向信息")
    orientation = np.asarray(first.image_orientation_patient).reshape(2, 3)
    if not np.all(np.isfinite(orientation)) or not np.allclose(
        orientation @ orientation.T, np.eye(2), atol=1e-4
    ):
        raise ValueError("3D 切片方向必须构成正交单位坐标轴")
    positions = np.array([item.image_position_patient for item in instances])
    if not np.all(np.isfinite(positions)):
        raise ValueError("3D 切片位置包含无效值")
    normal = np.cross(*orientation)
    positions = positions[np.argsort(positions @ normal)]
    steps = np.diff(positions, axis=0)
    spacing = float(np.median(steps @ normal))
    if spacing <= 1e-6 or not np.allclose(steps, normal*spacing, rtol=1e-3, atol=1e-3):
        raise ValueError("3D 暂不支持重复位置、不等距或存在层间偏移的切片")
