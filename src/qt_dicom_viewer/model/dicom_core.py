from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

from .dicom_types import InstanceDisplayMeta, WindowLevel

Vector3: TypeAlias = tuple[float, float, float]


def _index_to_reference_matrix(
    *,
    origin_reference: Vector3,
    axis0_direction: Vector3,
    axis1_direction: Vector3,
    axis2_direction: Vector3,
    axis0_spacing: float,
    axis1_spacing: float,
    axis2_spacing: float,
) -> np.ndarray:
    """构造三个索引轴到目标参考坐标系的齐次矩阵。"""
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, 0] = (
        np.asarray(axis0_direction, dtype=np.float64)
        * axis0_spacing
    )
    matrix[:3, 1] = (
        np.asarray(axis1_direction, dtype=np.float64)
        * axis1_spacing
    )
    matrix[:3, 2] = (
        np.asarray(axis2_direction, dtype=np.float64)
        * axis2_spacing
    )
    matrix[:3, 3] = np.asarray(
        origin_reference,
        dtype=np.float64,
    )
    #[
    #   [a0[0],a1[0], a2[0], origin[0]
    #   [a0[0],a1[0], a2[0], origin[0]
    #   [a0[0],a1[0], a2[0], origin[0]
    #   [0              ,0              ,               0, 1
    # ]
    return matrix


def _to_vector3(vector: np.ndarray) -> Vector3:
    return (
        float(vector[0]),
        float(vector[1]),
        float(vector[2]),
    )


@dataclass(frozen=True, slots=True)
class VolumeGeometry:
    slice_count: int
    rows: int
    columns: int

    row_spacing: float
    column_spacing: float
    slice_spacing: float

    origin_patient: Vector3
    #
    slice_index_direction_patient: Vector3
    row_index_direction_patient: Vector3
    column_index_direction_patient: Vector3

    @property
    def voxel_to_patient(self) -> np.ndarray:
        """将 Volume 体素坐标 (slice, row, column) 转为患者 LPS。"""
        return _index_to_reference_matrix(
            origin_reference=self.origin_patient,
            axis0_direction=self.slice_index_direction_patient,
            axis1_direction=self.row_index_direction_patient,
            axis2_direction=self.column_index_direction_patient,
            axis0_spacing=self.slice_spacing,
            axis1_spacing=self.row_spacing,
            axis2_spacing=self.column_spacing,
        )

    @property
    def patient_to_voxel(self) -> np.ndarray:
        """将患者 LPS 坐标转为 Volume 体素坐标 (slice, row, column)。"""
        return np.linalg.inv(self.voxel_to_patient)

    @property
    def center_patient(self) -> Vector3:
        """返回 Volume 几何中心在患者 LPS 中的位置。"""
        center_voxel = np.asarray(
            [
                (self.slice_count - 1) / 2.0,
                (self.rows - 1) / 2.0,
                (self.columns - 1) / 2.0,
                1.0,
            ],
            dtype=np.float64,
        )
        return _to_vector3(
            (self.voxel_to_patient @ center_voxel)[:3]
        )


@dataclass(slots=True)
class DicomVolume:
    modality_pixels: np.ndarray
    geometry: VolumeGeometry
    series_uid: str
    default_window: WindowLevel
    representative_instance_meta: InstanceDisplayMeta


@dataclass(frozen=True, slots=True)
class MprFrame:
    """以毫米为单位、嵌入患者 LPS 空间的 MPR 三维坐标系。"""

    center_patient: Vector3
    u_direction_patient: Vector3 = (1.0, 0.0, 0.0)
    v_direction_patient: Vector3 = (0.0, 1.0, 0.0)
    w_direction_patient: Vector3 = (0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        if not np.all(np.isfinite(self.center_patient)):
            raise ValueError("MPR center must be finite")
        basis = np.column_stack(
            (
                self.u_direction_patient,
                self.v_direction_patient,
                self.w_direction_patient,
            )
        ).astype(np.float64)
        if not np.all(np.isfinite(basis)):
            raise ValueError("MPR directions must be finite")
        if not np.allclose(
            basis.T @ basis,
            np.eye(3),
            rtol=1e-6,
            atol=1e-6,
        ):
            raise ValueError(
                "MPR directions must form an orthonormal basis"
            )
        if not np.isclose(
            np.linalg.det(basis),
            1.0,
            rtol=1e-6,
            atol=1e-6,
        ):
            raise ValueError(
                "MPR directions must form a right-handed basis"
            )

    @classmethod
    def standard_lps(cls, center_patient: Vector3) -> MprFrame:
        return cls(center_patient=center_patient)

    @property
    def mpr_to_patient(self) -> np.ndarray:
        """将 MPR 物理坐标 (u, v, w)，单位 mm，转为患者 LPS。"""
        return _index_to_reference_matrix(
            origin_reference=self.center_patient,
            axis0_direction=self.u_direction_patient,
            axis1_direction=self.v_direction_patient,
            axis2_direction=self.w_direction_patient,
            axis0_spacing=1.0,
            axis1_spacing=1.0,
            axis2_spacing=1.0,
        )

    @property
    def patient_to_mpr(self) -> np.ndarray:
        """将患者 LPS 转为以毫米为单位的 MPR 物理坐标。"""
        return np.linalg.inv(self.mpr_to_patient)

    def direction_to_patient(
        self,
        direction_mpr: Vector3,
    ) -> Vector3:
        direction = (
            self.mpr_to_patient[:3, :3]
            @ np.asarray(direction_mpr, dtype=np.float64)
        )
        return _to_vector3(direction)


@dataclass(frozen=True, slots=True)
class MprImageGeometry:
    """一张 MPR 输出图像的离散采样网格。"""

    rows: int
    columns: int
    row_spacing: float
    column_spacing: float
    normal_spacing: float

    frame: MprFrame
    top_left_mpr: Vector3
    row_direction_mpr: Vector3
    column_direction_mpr: Vector3
    navigation_direction_mpr: Vector3
    navigation_offset: float

    @property
    def image_index_to_mpr(self) -> np.ndarray:
        """将图像网格索引 (normal, row, column) 转为 MPR 毫米坐标。"""
        return _index_to_reference_matrix(
            origin_reference=self.top_left_mpr,
            axis0_direction=self.navigation_direction_mpr,
            axis1_direction=self.row_direction_mpr,
            axis2_direction=self.column_direction_mpr,
            axis0_spacing=self.normal_spacing,
            axis1_spacing=self.row_spacing,
            axis2_spacing=self.column_spacing,
        )

    @property
    def mpr_to_image_index(self) -> np.ndarray:
        return np.linalg.inv(self.image_index_to_mpr)

    def image_point_to_patient(
        self,
        *,
        column: float,
        row: float,
    ) -> Vector3:
        """将当前二维 MPR 图像坐标转换为患者 LPS 坐标。"""
        image_index = np.asarray(
            [0.0, row, column, 1.0],
            dtype=np.float64,
        )
        patient = self.image_index_to_patient @ image_index
        return _to_vector3(patient[:3])

    def mpr_point_to_image_point(
        self,
        point_mpr: Vector3,
    ) -> tuple[float, float]:
        """将 MPR 毫米坐标转换为当前图像的 (column, row)。"""
        image_index = self.mpr_to_image_index @ np.asarray(
            [*point_mpr, 1.0],
            dtype=np.float64,
        )
        return float(image_index[2]), float(image_index[1])

    @property
    def image_index_to_patient(self) -> np.ndarray:
        """将图像网格索引直接转为患者 LPS。"""
        return self.frame.mpr_to_patient @ self.image_index_to_mpr

    @property
    def patient_to_image_index(self) -> np.ndarray:
        return np.linalg.inv(self.image_index_to_patient)

    def image_index_to_voxel(
        self,
        volume_geometry: VolumeGeometry,
    ) -> np.ndarray:
        """将图像网格索引直接转为源 Volume 体素坐标。"""
        return (
            volume_geometry.patient_to_voxel
            @ self.image_index_to_patient
        )

    def voxel_to_image_index(
        self,
        volume_geometry: VolumeGeometry,
    ) -> np.ndarray:
        """将源 Volume 体素坐标直接转为图像网格索引。"""
        return (
            self.patient_to_image_index
            @ volume_geometry.voxel_to_patient
        )

    @property
    def top_left_patient(self) -> Vector3:
        point = self.frame.mpr_to_patient @ np.asarray(
            [*self.top_left_mpr, 1.0],
            dtype=np.float64,
        )
        return _to_vector3(point[:3])

    @property
    def row_direction_patient(self) -> Vector3:
        return self.frame.direction_to_patient(
            self.row_direction_mpr
        )

    @property
    def column_direction_patient(self) -> Vector3:
        return self.frame.direction_to_patient(
            self.column_direction_mpr
        )

    @property
    def navigation_direction_patient(self) -> Vector3:
        return self.frame.direction_to_patient(
            self.navigation_direction_mpr
        )

    @property
    def plane_normal_direction_patient(self) -> Vector3:
        normal = np.cross(
            np.asarray(self.column_direction_patient),
            np.asarray(self.row_direction_patient),
        )
        normal /= np.linalg.norm(normal)
        return _to_vector3(normal)

    @property
    def normal_coordinate_patient(self) -> float:
        return float(
            np.dot(
                self.top_left_patient,
                self.navigation_direction_patient,
            )
        )

    @property
    def image_orientation_patient(
        self,
    ) -> tuple[float, float, float, float, float, float]:
        # DICOM IOP 先保存列索引增加方向，再保存行索引增加方向。
        return (
            *self.column_direction_patient,
            *self.row_direction_patient,
        )


@dataclass(frozen=True, slots=True)
class MprSlice:
    modality_pixels: np.ndarray
    geometry: MprImageGeometry
    slice_index: int
    slice_count: int
