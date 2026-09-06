from __future__ import annotations

import numpy as np

from qt_dicom_viewer.model import MprPlane, MprProjectionMode
from qt_dicom_viewer.model.dicom_core import (
    DicomVolume,
    MprFrame,
    MprGridAnchor,
    MprGridSpec,
    MprImageGeometry,
    MprSlice,
    MprState,
    MprViewRolls,
    MprViewGrids,
)
from qt_dicom_viewer.core.mpr_rotation import resolve_sampling_basis


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
        view_roll_radians: float = 0.0,
        grid_spec: MprGridSpec | None = None,
        grid_anchor: MprGridAnchor | None = None,
        projection_mode: MprProjectionMode | None = None,
        slab_thickness_mm: float = 0.0,
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
        rolls = MprViewRolls()
        match plane:
            case MprPlane.AXIAL:
                rolls = MprViewRolls(axial_radians=view_roll_radians)
            case MprPlane.CORONAL:
                rolls = MprViewRolls(coronal_radians=view_roll_radians)
            case MprPlane.SAGITTAL:
                rolls = MprViewRolls(sagittal_radians=view_roll_radians)
            case _:
                raise MprResliceError(f"Unsupported MPR plane: {plane}")

        sampling_basis = resolve_sampling_basis(
            MprState(frame=resolved_frame, view_rolls=rolls),
            plane,
        )
        patient_to_mpr_direction = resolved_frame.patient_to_mpr[:3, :3]
        row_direction_mpr = patient_to_mpr_direction @ np.asarray(
            sampling_basis.row_direction_patient,
            dtype=np.float64,
        )
        column_direction_mpr = patient_to_mpr_direction @ np.asarray(
            sampling_basis.column_direction_patient,
            dtype=np.float64,
        )
        navigation_direction_mpr = patient_to_mpr_direction @ np.asarray(
            sampling_basis.navigation_direction_patient,
            dtype=np.float64,
        )
        # 将 Volume 的 8 个极端体素中心转到 MPR 物理坐标系。
        # 后续范围计算均以 MPR Frame 原点为原点，单位为 mm。
        volume_corner_centers_mpr = self._volume_corners_mpr(
            volume,
            resolved_frame,
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

        navigation_extent = (
            navigation_bounds[1] - navigation_bounds[0]
        )

        # 根据每个输出轴在源 Volume 中跨越体素索引的速度，
        # 估算对应的首选采样间距。对于轴对齐 Volume，
        # Axial/Coronal/Sagittal 的导航层数会分别对应源数据的
        # depth/height/width。Oblique MPR 后续可以使用独立的采样策略。
        row_direction_patient = np.asarray(
            sampling_basis.row_direction_patient
        )
        column_direction_patient = np.asarray(
            sampling_basis.column_direction_patient
        )
        navigation_direction_patient = np.asarray(
            sampling_basis.navigation_direction_patient
        )
        preferred_navigation_spacing = self._spacing_along_direction(
            volume,
            navigation_direction_patient,
        )
        if grid_spec is None:
            row_bounds = self._project_bounds(
                volume_corner_centers_mpr,
                row_direction_mpr,
            )
            column_bounds = self._project_bounds(
                volume_corner_centers_mpr,
                column_direction_mpr,
            )
            row_extent = row_bounds[1] - row_bounds[0]
            column_extent = column_bounds[1] - column_bounds[0]
            preferred_row_spacing = self._spacing_along_direction(
                volume,
                row_direction_patient,
            )
            preferred_column_spacing = self._spacing_along_direction(
                volume,
                column_direction_patient,
            )
            row_spacing = self._bounded_axis_spacing(
                preferred_spacing=preferred_row_spacing,
                extent=row_extent,
            )
            column_spacing = self._bounded_axis_spacing(
                preferred_spacing=preferred_column_spacing,
                extent=column_extent,
            )
            grid_spec = MprGridSpec(
                rows=self._sample_count(row_extent, row_spacing),
                columns=self._sample_count(
                    column_extent,
                    column_spacing,
                ),
                row_spacing=row_spacing,
                column_spacing=column_spacing,
            )

        # 有了固定网格后，旋转只会改变采样方向，不再改变
        # 输出数组尺寸和毫米间距。
        rows = grid_spec.rows
        columns = grid_spec.columns
        row_spacing = grid_spec.row_spacing
        column_spacing = grid_spec.column_spacing
        resolved_anchor = grid_anchor or MprGridAnchor.centered(grid_spec)

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
        # anchor 表示 MPR Frame 中心应该落在固定网格的哪个
        # 连续索引上。移动十字线时改变 anchor，可以在网格大小
        # 不变的同时保持源视图的采样原点不动。
        image_origin_mpr = (
            -column_direction_mpr
            * resolved_anchor.column
            * grid_spec.column_spacing
            - row_direction_mpr
            * resolved_anchor.row
            * grid_spec.row_spacing
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
        if (
            not np.isfinite(slab_thickness_mm)
            or not 0 <= slab_thickness_mm <= 100
        ):
            raise MprResliceError(
                "Slab thickness must be between 0 and 100 mm"
            )

        # 关闭投影或厚度为零时仍走原有单平面路径，保证结果与旧版本一致。
        if projection_mode is None or slab_thickness_mm == 0:
            modality_pixels = self._sample_plane(
                volume=volume,
                geometry=plane_geometry,
            )
        else:
            modality_pixels = self._sample_slab(
                volume=volume,
                geometry=plane_geometry,
                mode=projection_mode,
                thickness_mm=slab_thickness_mm,
            )

        return MprSlice(
            modality_pixels=modality_pixels,
            geometry=plane_geometry,
            slice_index=navigation_index,
            slice_count=navigation_count,
        )

    def create_view_grids(
        self,
        volume: DicomVolume,
        frame: MprFrame | None = None,
    ) -> MprViewGrids:
        """按初始 MPR 方向为三个视图生成一次性固定网格。"""
        resolved_frame = frame or MprFrame.standard_lps(
            volume.geometry.center_patient
        )
        return MprViewGrids(
            axial=self._create_grid_spec(
                volume,
                resolved_frame,
                MprPlane.AXIAL,
            ),
            coronal=self._create_grid_spec(
                volume,
                resolved_frame,
                MprPlane.CORONAL,
            ),
            sagittal=self._create_grid_spec(
                volume,
                resolved_frame,
                MprPlane.SAGITTAL,
            ),
        )

    def _create_grid_spec(
        self,
        volume: DicomVolume,
        frame: MprFrame,
        plane: MprPlane,
    ) -> MprGridSpec:
        """根据初始方向下 Volume 的投影范围构造固定网格。"""
        sampling_basis = resolve_sampling_basis(
            MprState(frame=frame),
            plane,
        )
        patient_to_mpr_direction = frame.patient_to_mpr[:3, :3]
        row_direction_mpr = patient_to_mpr_direction @ np.asarray(
            sampling_basis.row_direction_patient,
            dtype=np.float64,
        )
        column_direction_mpr = patient_to_mpr_direction @ np.asarray(
            sampling_basis.column_direction_patient,
            dtype=np.float64,
        )
        corners_mpr = self._volume_corners_mpr(volume, frame)
        row_bounds = self._project_bounds(corners_mpr, row_direction_mpr)
        column_bounds = self._project_bounds(
            corners_mpr,
            column_direction_mpr,
        )
        row_extent = row_bounds[1] - row_bounds[0]
        column_extent = column_bounds[1] - column_bounds[0]
        row_spacing = self._bounded_axis_spacing(
            preferred_spacing=self._spacing_along_direction(
                volume,
                np.asarray(sampling_basis.row_direction_patient),
            ),
            extent=row_extent,
        )
        column_spacing = self._bounded_axis_spacing(
            preferred_spacing=self._spacing_along_direction(
                volume,
                np.asarray(sampling_basis.column_direction_patient),
            ),
            extent=column_extent,
        )
        return MprGridSpec(
            rows=self._sample_count(row_extent, row_spacing),
            columns=self._sample_count(
                column_extent,
                column_spacing,
            ),
            row_spacing=row_spacing,
            column_spacing=column_spacing,
        )

    def _sample_plane(
        self,
        volume: DicomVolume,
        geometry: MprImageGeometry,
        navigation_offset_mm: float = 0.0,
    ) -> np.ndarray:
        """把 MPR 输出网格映射到源体素坐标并完成采样。"""

        # 采样网格索引 → MPR → 患者 → 源体素。矩阵列依次表示
        # navigation offset、row、column 索引各增加 1 时，
        # 源体素坐标的变化。
        image_to_voxel = geometry.image_index_to_voxel(
            volume.geometry
        )
        voxel_origin = (
            image_to_voxel[:3, 3]
            + image_to_voxel[:3, 0]
            * (navigation_offset_mm / geometry.navigation_spacing)
        )
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

    def _sample_slab(
        self,
        volume: DicomVolume,
        geometry: MprImageGeometry,
        mode: MprProjectionMode,
        thickness_mm: float,
    ) -> np.ndarray:
        """沿平面法线对称采样，并以常量内存完成厚层投影。"""

        half_thickness = thickness_mm / 2.0
        half_interval_count = max(
            1,
            int(np.ceil(half_thickness / geometry.navigation_spacing)),
        )
        offsets = np.linspace(
            -half_thickness,
            half_thickness,
            2 * half_interval_count + 1,
            dtype=np.float64,
        )

        shape = (geometry.rows, geometry.columns)
        valid_count = np.zeros(shape, dtype=np.int32)

        if mode == MprProjectionMode.MIN_IP:
            aggregate = np.full(shape, np.inf, dtype=np.float32)
        elif mode == MprProjectionMode.MIP:
            aggregate = np.full(shape, -np.inf, dtype=np.float32)
        elif mode in (MprProjectionMode.MEAN, MprProjectionMode.SUM):
            # 累加使用 float64，降低厚层 Sum/Mean 的累计舍入误差。
            aggregate = np.zeros(shape, dtype=np.float64)
        else:
            raise MprResliceError(
                f"Unsupported MPR projection mode: {mode}"
            )

        for offset in offsets:
            sampled = self._sample_plane(
                volume,
                geometry,
                navigation_offset_mm=float(offset),
            )
            valid = np.isfinite(sampled)
            valid_count[valid] += 1

            if mode == MprProjectionMode.MIN_IP:
                aggregate[valid] = np.minimum(
                    aggregate[valid],
                    sampled[valid],
                )
            elif mode == MprProjectionMode.MIP:
                aggregate[valid] = np.maximum(
                    aggregate[valid],
                    sampled[valid],
                )
            else:
                aggregate[valid] += sampled[valid]

        has_value = valid_count > 0
        if mode == MprProjectionMode.MEAN:
            np.divide(
                aggregate,
                valid_count,
                out=aggregate,
                where=has_value,
            )

        result = np.asarray(aggregate, dtype=np.float32)
        result[~has_value] = np.nan
        return np.ascontiguousarray(result)

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

        numerator = np.zeros_like(slices, dtype=np.float64)
        denominator = np.zeros_like(slices, dtype=np.float64)
        values = (value000, value001, value010, value011,
                  value100, value101, value110, value111)
        for index, value in enumerate(values):
            weight = ((slice_weight if index & 4 else 1 - slice_weight)
                      * (row_weight if index & 2 else 1 - row_weight)
                      * (column_weight if index & 1 else 1 - column_weight))
            supported = np.isfinite(value) & (weight > 0)
            numerator += np.where(supported, value, 0) * weight
            denominator += np.where(supported, weight, 0)
        sampled = np.full(slices.shape, np.nan, dtype=np.float32)
        np.divide(numerator, denominator, out=sampled, where=denominator > 0)

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
    def _to_vector3(
        vector: np.ndarray,
    ) -> tuple[float, float, float]:
        return (
            float(vector[0]),
            float(vector[1]),
            float(vector[2]),
        )
