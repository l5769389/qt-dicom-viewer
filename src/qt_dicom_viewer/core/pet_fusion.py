"""Rigid PET→CT geometry, registration interchange and scalar compositing."""
from dataclasses import replace, asdict
from hashlib import sha256
import json
from math import radians

import numpy as np

from qt_dicom_viewer.core.mpr_rotation import axis_angle_rotation_matrix


def fusion_series_error(series):
    from qt_dicom_viewer.core.volume_view import validate_volume_series
    from qt_dicom_viewer.core.volume_manager import VolumeManager
    from qt_dicom_viewer.core.pet import validate_pet_2d_series
    try:
        if series.modality.upper() not in ("CT", "PT"):
            raise ValueError("融合只支持 CT 和 PET")
        validate_pet_2d_series(series)
        validate_volume_series(series)
        VolumeManager._validate_instances(series.instances)
        first = series.instances[0]
        for item in series.instances:
            VolumeManager._validate_instance_geometry(item, first.rows, first.columns,
                first.pixel_spacing.row, first.pixel_spacing.column,
                np.asarray(first.image_orientation_patient))
        if len({i.frame_of_reference_uid for i in series.instances}) != 1:
            raise ValueError("同一序列的 FrameOfReferenceUID 不一致")
        return ""
    except (ValueError, RuntimeError, TypeError) as error:
        return str(error).replace("3D", "MPR/融合")


def rigid_matrix(matrix):
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.size != 16:
        raise ValueError("配准矩阵必须是 4×4")
    matrix = matrix.reshape(4, 4)
    rotation = matrix[:3, :3]
    if (not np.isfinite(matrix).all() or
            not np.allclose(matrix[3], (0, 0, 0, 1), atol=1e-7, rtol=0) or
            not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6, rtol=0) or
            not np.isclose(np.linalg.det(rotation), 1, atol=1e-6, rtol=0)):
        raise ValueError("配准矩阵必须是有限的刚性平移/旋转矩阵")
    return matrix.copy()


def registration_from_parameters(translation, angles_degrees, pivot):
    values = np.asarray([*translation, *angles_degrees, *pivot], dtype=float)
    if values.shape != (9,) or not np.isfinite(values).all():
        raise ValueError("配准参数必须是有限数值")
    rotations = [axis_angle_rotation_matrix(tuple(np.eye(3)[i]), radians(a))
                 for i, a in enumerate(angles_degrees)]
    rotation = rotations[2] @ rotations[1] @ rotations[0]
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = np.asarray(translation) + pivot - rotation @ pivot
    return matrix


def parameters_from_registration(matrix, pivot):
    matrix = rigid_matrix(matrix)
    r = matrix[:3, :3]
    y = np.arcsin(np.clip(-r[2, 0], -1, 1))
    if abs(np.cos(y)) > 1e-7:
        x, z = np.arctan2(r[2, 1], r[2, 2]), np.arctan2(r[1, 0], r[0, 0])
    else:
        x, z = np.arctan2(-r[1, 2], r[1, 1]), 0.
    translation = matrix[:3, 3] - pivot + r @ pivot
    return translation, np.degrees((x, y, z))


def transformed_volume(volume, matrix):
    matrix = rigid_matrix(matrix)
    g = volume.geometry
    r = matrix[:3, :3]
    geometry = replace(g, origin_patient=tuple(r @ g.origin_patient + matrix[:3, 3]),
                       slice_index_direction_patient=tuple(r @ g.slice_index_direction_patient),
                       row_index_direction_patient=tuple(r @ g.row_index_direction_patient),
                       column_index_direction_patient=tuple(r @ g.column_index_direction_patient))
    return replace(volume, geometry=geometry)


def geometry_fingerprint(volume):
    return sha256(json.dumps(asdict(volume.geometry), sort_keys=True).encode()).hexdigest()


def registration_document(ct, pet, ct_for, pet_for, matrix, pivot):
    return dict(version=1, direction="PET_LPS_TO_CT_LPS", ctSeriesUID=ct.series_uid,
                petSeriesUID=pet.series_uid, ctFrameOfReferenceUID=ct_for,
                petFrameOfReferenceUID=pet_for, ctGeometry=geometry_fingerprint(ct),
                petGeometry=geometry_fingerprint(pet), matrix=rigid_matrix(matrix).tolist(),
                pivot=np.asarray(pivot, dtype=float).tolist())


def load_registration_document(document, expected):
    if not isinstance(document, dict):
        raise ValueError("配准 JSON 必须是版本化对象")
    for key in ("version", "direction", "ctSeriesUID", "petSeriesUID",
                "ctFrameOfReferenceUID", "petFrameOfReferenceUID", "ctGeometry", "petGeometry"):
        if document.get(key) != expected.get(key):
            raise ValueError(f"配准文件与当前序列不匹配：{key}")
    pivot = np.asarray(document.get("pivot"), dtype=float)
    if pivot.shape != (3,) or not np.isfinite(pivot).all():
        raise ValueError("配准旋转中心无效")
    return rigid_matrix(document.get("matrix")), pivot


def pet_rgb(gray, color_map):
    x = np.asarray(gray, dtype=np.float32) / 255.
    if color_map == "grayscale":
        return np.repeat(gray[..., None], 3, axis=-1)
    if color_map != "hotIron":
        raise ValueError("不支持的 PET 色表")
    return np.round(np.stack((np.clip(3*x, 0, 1), np.clip(3*x-1, 0, 1),
                              np.clip(3*x-2, 0, 1)), axis=-1) * 255).astype(np.uint8)


def blend_pet_ct(ct_gray, pet_gray, pet_values, opacity, color_map="hotIron"):
    if not np.isfinite(opacity) or not 0 <= opacity <= 1:
        raise ValueError("融合透明度必须在 0–1 之间")
    ct = np.repeat(ct_gray[..., None], 3, axis=-1).astype(np.float32)
    rgb = pet_rgb(pet_gray, color_map).astype(np.float32)
    alpha = (opacity * (np.isfinite(pet_values) & (pet_values > 0)))[..., None]
    return np.ascontiguousarray(np.round(ct * (1-alpha) + rgb * alpha), dtype=np.uint8)
