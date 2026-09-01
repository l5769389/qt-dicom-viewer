from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

from .dicom_types import InstanceDisplayMeta, WindowLevel

Vector3: TypeAlias = tuple[float, float, float]


def _affine_from_basis(
    *,
    origin_in_target: Vector3,
    axis0_direction_in_target: Vector3,
    axis1_direction_in_target: Vector3,
    axis2_direction_in_target: Vector3,
    axis0_spacing: float,
    axis1_spacing: float,
    axis2_spacing: float,
) -> np.ndarray:
    """用原点和三个基轴构造到目标坐标系的齐次仿射矩阵。

    输入坐标的三个分量分别沿 axis0/axis1/axis2 增加；
    矩阵的每一列表示对应分量增加 1 时，在目标坐标系中的位移。
    """
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, 0] = (
        np.asarray(axis0_direction_in_target, dtype=np.float64)
        * axis0_spacing
    )
    matrix[:3, 1] = (
        np.asarray(axis1_direction_in_target, dtype=np.float64)
        * axis1_spacing
    )
    matrix[:3, 2] = (
        np.asarray(axis2_direction_in_target, dtype=np.float64)
        * axis2_spacing
    )
    matrix[:3, 3] = np.asarray(
        origin_in_target,
        dtype=np.float64,
    )
    # [
    #   [axis0.x, axis1.x, axis2.x, origin.x],
    #   [axis0.y, axis1.y, axis2.y, origin.y],
    #   [axis0.z, axis1.z, axis2.z, origin.z],
    #   [0.0,     0.0,     0.0,     1.0],
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
        # 这里的体素坐标可以是用于插值的连续索引，不仅是整数索引。
        return _affine_from_basis(
            origin_in_target=self.origin_patient,
            axis0_direction_in_target=(
                self.slice_index_direction_patient
            ),
            axis1_direction_in_target=self.row_index_direction_patient,
            axis2_direction_in_target=(
                self.column_index_direction_patient
            ),
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
        return _affine_from_basis(
            origin_in_target=self.center_patient,
            axis0_direction_in_target=self.u_direction_patient,
            axis1_direction_in_target=self.v_direction_patient,
            axis2_direction_in_target=self.w_direction_patient,
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
    """一张 MPR 输出图像及其导航轴的采样几何。"""

    rows: int
    columns: int
    row_spacing: float
    column_spacing: float
    navigation_spacing: float

    frame: MprFrame
    image_origin_mpr: Vector3
    row_direction_mpr: Vector3
    column_direction_mpr: Vector3
    navigation_direction_mpr: Vector3

    @property
    def image_index_to_mpr(self) -> np.ndarray:
        """将采样网格索引转为 MPR 毫米坐标。

        索引顺序是 (navigation_offset_index, row_index, column_index)。
        第 0 轴是相对于当前平面的导航偏移，不是 MprSlice.slice_index。
        """
        return _affine_from_basis(
            origin_in_target=self.image_origin_mpr,
            axis0_direction_in_target=(
                self.navigation_direction_mpr
            ),
            axis1_direction_in_target=self.row_direction_mpr,
            axis2_direction_in_target=self.column_direction_mpr,
            axis0_spacing=self.navigation_spacing,
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
    def image_origin_patient(self) -> Vector3:
        """返回输出图像第一个像素中心在患者 LPS 中的位置。"""
        point = self.frame.mpr_to_patient @ np.asarray(
            [*self.image_origin_mpr, 1.0],
            dtype=np.float64,
        )
        return _to_vector3(point[:3])

    @property
    def plane_offset_mpr(self) -> float:
        """返回当前平面沿导航轴相对 MPR Frame 原点的偏移。"""
        return float(
            np.dot(
                self.image_origin_mpr,
                self.navigation_direction_mpr,
            )
        )

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
    def iop_normal_direction_patient(self) -> Vector3:
        """返回由图像 IOP 两个方向叉乘得到的有向法线。"""
        normal = np.cross(
            np.asarray(self.column_direction_patient),
            np.asarray(self.row_direction_patient),
        )
        normal /= np.linalg.norm(normal)
        return _to_vector3(normal)

    @property
    def navigation_position_patient(self) -> float:
        """返回图像原点沿导航方向的标量位置。

        这个值用于界面显示切片位置，使其随 navigation index
        递增。它不是由 IOP 叉乘法线强制定义的 DICOM 值。
        """
        return float(
            np.dot(
                self.image_origin_patient,
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
    """当前 MPR 平面及其在导航范围内的离散编号。"""

    modality_pixels: np.ndarray
    geometry: MprImageGeometry
    slice_index: int
    slice_count: int
