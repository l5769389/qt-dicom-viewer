from __future__ import annotations

import numpy as np

from qt_dicom_viewer.model import MprPlane
from qt_dicom_viewer.model.dicom_core import (
    DicomVolume,
    MprFrame,
    MprImageGeometry,
    MprSlice,
)


class MprResliceError(RuntimeError):
    pass


class MprReslicer:
    """从源 DICOM 体数据中重采样标准解剖平面。"""

    def __init__(self, max_output_dimension: int = 1024) -> None:
        if max_output_dimension < 2:
            raise ValueError(
                "max_output_dimension must be at least 2"
            )
        self._max_output_dimension = max_output_dimension

    def reslice(
        self,
        volume: DicomVolume,
        plane: MprPlane,
        frame: MprFrame | None = None,
    ) -> MprSlice:
        """从任意朝向的源 Volume 中重采样一个 MPR 平面。

        先在 MPR 物理坐标系中定义二维采样网格，再依次映射到患者
        LPS 和源 Volume 连续体素坐标，最后通过插值得到模态像素值。
        """

        # 确定本次重采样使用的 MPR Frame。未传入 Frame 时，
        # 以 Volume 中心为原点，并使 U/V/W 轴与患者 LPS 对齐。
        resolved_frame = frame or MprFrame.standard_lps(
            volume.geometry.center_patient
        )
        # - row_direction_mpr：图像 row 增大时，在 MPR 中向哪里移动。
        # - column_direction_mpr：图像 column 增大时，在 MPR 中向哪里移动。
        # - navigation_direction_mpr：切片索引增大时，在 MPR 中向哪里移动。
        (
            row_direction_mpr,
            column_direction_mpr,
            navigation_direction_mpr,
        ) = self._plane_axes_mpr(plane)
        # 将 Volume 的 8 个极端体素中心转到 MPR 物理坐标系。
        # 后续范围计算均以 MPR Frame 原点为原点，单位为 mm。
        volume_corner_centers_mpr = self._volume_corners_mpr(
            volume,
            resolved_frame,
        )
        row_bounds = self._project_bounds(
            volume_corner_centers_mpr,
            row_direction_mpr,
        )
        column_bounds = self._project_bounds(
            volume_corner_centers_mpr,
            column_direction_mpr,
        )
        navigation_bounds = self._project_bounds(
            volume_corner_centers_mpr,
            navigation_direction_mpr,
        )
        source_spacings = (
            volume.geometry.slice_spacing,
            volume.geometry.row_spacing,
            volume.geometry.column_spacing,
        )
        if any(
            not np.isfinite(spacing) or spacing <= 0
            for spacing in source_spacings
        ):
            raise MprResliceError(
                "Volume contains an invalid voxel spacing"
            )

        row_extent = row_bounds[1] - row_bounds[0]
        column_extent = column_bounds[1] - column_bounds[0]
        navigation_extent = (
            navigation_bounds[1] - navigation_bounds[0]
        )

        # 根据每个输出轴在源 Volume 中跨越体素索引的速度，
        # 估算对应的首选采样间距。对于轴对齐 Volume，
        # Axial/Coronal/Sagittal 的导航层数会分别对应源数据的
        # depth/height/width。Oblique MPR 后续可以使用独立的采样策略。
        row_direction_patient = np.asarray(
            resolved_frame.direction_to_patient(
                self._to_vector3(row_direction_mpr)
            )
        )
        column_direction_patient = np.asarray(
            resolved_frame.direction_to_patient(
                self._to_vector3(column_direction_mpr)
            )
        )
        navigation_direction_patient = np.asarray(
            resolved_frame.direction_to_patient(
                self._to_vector3(navigation_direction_mpr)
            )
        )
        preferred_row_spacing = self._spacing_along_direction(
            volume,
            row_direction_patient,
        )
        preferred_column_spacing = self._spacing_along_direction(
            volume,
            column_direction_patient,
        )
        preferred_navigation_spacing = self._spacing_along_direction(
            volume,
            navigation_direction_patient,
        )
        row_spacing = self._bounded_axis_spacing(
            preferred_spacing=preferred_row_spacing,
            extent=row_extent,
        )
        column_spacing = self._bounded_axis_spacing(
            preferred_spacing=preferred_column_spacing,
            extent=column_extent,
        )
        # 计算输出宽高和切片数量
        rows = self._sample_count(
            row_extent,
            row_spacing,
        )
        columns = self._sample_count(
            column_extent,
            column_spacing,
        )

        navigation_count = self._sample_count(
            # 正交 MPR 的导航切片总数使用当前导航轴的首选间距，
            # 因此轴对齐
            # Volume 会得到 depth/height/width，而不是最小 spacing
            # 各向同性重采样后产生的额外插值层。
            navigation_extent,
            preferred_navigation_spacing,
        )
        # 重新从物理范围计算最终间距，使第一层和最后一层准确落在两端，
        # 同时消除 DICOM 浮点位置造成的微小累计误差。
        navigation_spacing = (
            navigation_extent / (navigation_count - 1)
            if navigation_count > 1
            else preferred_navigation_spacing
        )
        # MPR 平面始终穿过 Frame 原点。slice_index 只是把这个物理位置
        # 映射到导航范围内最接近的离散编号，用于界面显示。
        navigation_index = self._index_nearest_origin(
            navigation_count,
            navigation_bounds,
            navigation_spacing,
        )
        plane_offset_mpr = 0.0
        # 第一个输出像素中心由 row/column 的最小投影坐标
        # 和当前平面沿导航轴的偏移共同确定。
        image_origin_mpr = (
            column_direction_mpr * column_bounds[0]
            + row_direction_mpr * row_bounds[0]
            + navigation_direction_mpr * plane_offset_mpr
        )
        plane_geometry = MprImageGeometry(
            rows=rows,
            columns=columns,
            row_spacing=row_spacing,
            column_spacing=column_spacing,
            navigation_spacing=navigation_spacing,
            frame=resolved_frame,
            image_origin_mpr=self._to_vector3(image_origin_mpr),
            row_direction_mpr=self._to_vector3(
                row_direction_mpr
            ),
            column_direction_mpr=self._to_vector3(
                column_direction_mpr
            ),
            navigation_direction_mpr=self._to_vector3(
                navigation_direction_mpr
            ),
        )
        # 生成整个输出采样网格
        modality_pixels = self._sample_plane(
            volume=volume,
            geometry=plane_geometry,
        )

        return MprSlice(
            modality_pixels=modality_pixels,
            geometry=plane_geometry,
            slice_index=navigation_index,
            slice_count=navigation_count,
        )

    def _sample_plane(
        self,
        volume: DicomVolume,
        geometry: MprImageGeometry,
    ) -> np.ndarray:
        """把 MPR 输出网格映射到源体素坐标并完成采样。"""

        # 采样网格索引 → MPR → 患者 → 源体素。矩阵列依次表示
        # navigation offset、row、column 索引各增加 1 时，
        # 源体素坐标的变化。
        image_to_voxel = geometry.image_index_to_voxel(
            volume.geometry
        )
        voxel_origin = image_to_voxel[:3, 3]
        voxel_row_step = image_to_voxel[:3, 1]
        voxel_column_step = image_to_voxel[:3, 2]

        row_indices = np.arange(
            # (rows, 1) 与 (1, columns) 通过广播生成完整二维坐标网格。
            geometry.rows,
            dtype=np.float64,
        )[:, None]
        column_indices = np.arange(
            geometry.columns,
            dtype=np.float64,
        )[None, :]

        slice_coordinates = (
            voxel_origin[0]
            + row_indices * voxel_row_step[0]
            + column_indices * voxel_column_step[0]
        )
        row_coordinates = (
            voxel_origin[1]
            + row_indices * voxel_row_step[1]
            + column_indices * voxel_column_step[1]
        )
        column_coordinates = (
            voxel_origin[2]
            + row_indices * voxel_row_step[2]
            + column_indices * voxel_column_step[2]
        )
        # 三线性插值
        return self._trilinear_sample(
            volume.modality_pixels,
            slice_coordinates,
            row_coordinates,
            column_coordinates,
        )

    @staticmethod
    def _trilinear_sample(
        volume: np.ndarray,
        slice_coordinates: np.ndarray,
        row_coordinates: np.ndarray,
        column_coordinates: np.ndarray,
    ) -> np.ndarray:
        """对一组连续体素坐标执行三线性插值。"""

        if volume.ndim != 3:
            raise MprResliceError(
                f"Expected a 3D volume, got shape={volume.shape}"
            )

        slice_max, row_max, column_max = (
            size - 1 for size in volume.shape
        )
        epsilon = 1e-6
        # 倾斜 Volume 的矩形投影可能包含体数据之外的点。先记录有效性，
        # 再裁剪坐标以保证后续数组索引安全。
        valid = (
            (slice_coordinates >= -epsilon)
            & (slice_coordinates <= slice_max + epsilon)
            & (row_coordinates >= -epsilon)
            & (row_coordinates <= row_max + epsilon)
            & (column_coordinates >= -epsilon)
            & (column_coordinates <= column_max + epsilon)
        )

        slices = np.clip(
            slice_coordinates,
            0,
            slice_max,
        )
        rows = np.clip(
            row_coordinates,
            0,
            row_max,
        )
        columns = np.clip(
            column_coordinates,
            0,
            column_max,
        )

        slice0 = np.floor(slices).astype(np.intp)
        # 三个轴上的向下和向上取整确定周围 8 个源体素；坐标的小数部分
        # 作为后续插值权重。
        row0 = np.floor(rows).astype(np.intp)
        column0 = np.floor(columns).astype(np.intp)
        slice1 = np.minimum(slice0 + 1, slice_max)
        row1 = np.minimum(row0 + 1, row_max)
        column1 = np.minimum(column0 + 1, column_max)

        slice_weight = slices - slice0
        row_weight = rows - row0
        column_weight = columns - column0

        value000 = volume[slice0, row0, column0]
        value001 = volume[slice0, row0, column1]
        value010 = volume[slice0, row1, column0]
        value011 = volume[slice0, row1, column1]
        value100 = volume[slice1, row0, column0]
        value101 = volume[slice1, row0, column1]
        value110 = volume[slice1, row1, column0]
        value111 = volume[slice1, row1, column1]

        value00 = (
            # 依次沿 column（8→4）、row（4→2）、slice（2→1）插值。
            value000 * (1.0 - column_weight)
            + value001 * column_weight
        )
        value01 = (
            value010 * (1.0 - column_weight)
            + value011 * column_weight
        )
        value10 = (
            value100 * (1.0 - column_weight)
            + value101 * column_weight
        )
        value11 = (
            value110 * (1.0 - column_weight)
            + value111 * column_weight
        )
        value0 = (
            value00 * (1.0 - row_weight)
            + value01 * row_weight
        )
        value1 = (
            value10 * (1.0 - row_weight)
            + value11 * row_weight
        )
        sampled = (
            value0 * (1.0 - slice_weight)
            + value1 * slice_weight
        ).astype(np.float32)

        # Volume 之外的位置保留为缺失模态值；apply_window 会将其显示为背景。
        sampled[~valid] = np.nan
        return np.ascontiguousarray(sampled)

    def _bounded_axis_spacing(
        self,
        preferred_spacing: float,
        extent: float,
    ) -> float:
        maximum_intervals = self._max_output_dimension - 1
        return max(
            preferred_spacing,
            extent / maximum_intervals,
        )

    @staticmethod
    def _spacing_along_direction(
        volume: DicomVolume,
        patient_direction: np.ndarray,
    ) -> float:
        # 沿 row_direction_patient 在患者空间移动 1 mm。
        # 看这 1 mm 会跨过多少个 Volume 体素索引。
        # 取倒数，得到该方向上一个采样步长大约对应多少 mm。
        voxel_step_per_mm = (
            volume.geometry.patient_to_voxel[:3, :3]
            @ patient_direction
        )
        voxel_steps = float(np.linalg.norm(voxel_step_per_mm))
        if not np.isfinite(voxel_steps) or voxel_steps <= 1e-12:
            raise MprResliceError(
                "Cannot resolve spacing along MPR direction"
            )
        return 1.0 / voxel_steps

    @staticmethod
    def _sample_count(
        extent: float,
        spacing: float,
    ) -> int:
        if extent <= 1e-8:
            return 1

        intervals = extent / spacing
        nearest_integer = round(intervals)
        # DICOM 方向和位置经过矩阵运算后，理论整数可能成为
        # 319.00000000000006。若直接 ceil 会把 320 个采样点误算为 321。
        if np.isclose(
            intervals,
            nearest_integer,
            rtol=1e-9,
            atol=1e-7,
        ):
            intervals = float(nearest_integer)

        return max(
            2,
            int(np.ceil(intervals)) + 1,
        )

    @staticmethod
    def _index_nearest_origin(
        navigation_count: int,
        navigation_bounds: tuple[float, float],
        navigation_spacing: float,
    ) -> int:
        nearest_index = int(
            np.floor(
                (-navigation_bounds[0]) / navigation_spacing
                + 0.5
            )
        )
        return min(
            max(nearest_index, 0),
            navigation_count - 1,
        )

    @staticmethod
    def _project_bounds(
        points: np.ndarray,
        direction: np.ndarray,
    ) -> tuple[float, float]:
        """返回角点沿指定 MPR 轴投影后的坐标范围。"""
        projected = points @ direction
        return float(np.min(projected)), float(np.max(projected))

    @staticmethod
    def _volume_corners_mpr(
        volume: DicomVolume,
        frame: MprFrame,
    ) -> np.ndarray:
        """返回源 Volume 的 8 个极端体素中心在 MPR 中的毫米坐标。"""
        slice_max = volume.geometry.slice_count - 1
        row_max = volume.geometry.rows - 1
        column_max = volume.geometry.columns - 1
        corners = np.asarray(
            [
                (slice_index, row_index, column_index, 1.0)
                for slice_index in (0, slice_max)
                for row_index in (0, row_max)
                for column_index in (0, column_max)
            ],
            dtype=np.float64,
        )
        mpr = (
            frame.patient_to_mpr
            @ volume.geometry.voxel_to_patient
            @ corners.T
        ).T
        return mpr[:, :3]

    @staticmethod
    def _plane_axes_mpr(
        plane: MprPlane,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """返回图像向下、向右和翻到下一层的 MPR 方向。"""
        # 三个视图从同一个 MPR U/V/W 坐标系派生。这里的向量位于
        # MPR 局部坐标中；MprFrame 再负责把它们转换到患者 LPS。
        match plane:
            case MprPlane.AXIAL:
                # 屏幕向下 +V，向右 +U，沿 +W 翻页。
                row = (0.0, 1.0, 0.0)
                column = (1.0, 0.0, 0.0)
                navigation = (0.0, 0.0, 1.0)
            case MprPlane.CORONAL:
                # 屏幕向下 -W，向右 +U，沿 +V 翻页。
                row = (0.0, 0.0, -1.0)
                column = (1.0, 0.0, 0.0)
                navigation = (0.0, 1.0, 0.0)
            case MprPlane.SAGITTAL:
                # 屏幕向下 -W，向右 +V，沿 +U 翻页。
                row = (0.0, 0.0, -1.0)
                column = (0.0, 1.0, 0.0)
                navigation = (1.0, 0.0, 0.0)
            case _:
                raise MprResliceError(
                    f"Unsupported MPR plane: {plane}"
                )

        return (
            np.asarray(row, dtype=np.float64),
            np.asarray(column, dtype=np.float64),
            np.asarray(navigation, dtype=np.float64),
        )

    @staticmethod
    def _to_vector3(
        vector: np.ndarray,
    ) -> tuple[float, float, float]:
        return (
            float(vector[0]),
            float(vector[1]),
            float(vector[2]),
        )
