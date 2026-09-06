from __future__ import annotations

import logging
from dataclasses import replace
from hashlib import sha256

import numpy as np
import pydicom

from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.model import (
    DicomInstanceMeta,
    DicomSeriesRecord,
    InstanceDisplayMeta,
    WindowLevel,
    PixelValueMeta,
)
from qt_dicom_viewer.model.dicom_core import (
    DicomVolume,
    VolumeGeometry,
)

logger = logging.getLogger(__name__)


class VolumeBuildError(RuntimeError):
    pass


class VolumeManager:
    def __init__(self) -> None:
        self._volumes_by_series_uid: dict[
            tuple[str, int | None], DicomVolume
        ] = {}

    def get_volume(
        self,
        series_uid: str,
        phase_identifier: int | None = None,
    ) -> DicomVolume | None:
        return self._volumes_by_series_uid.get(
            (series_uid, phase_identifier)
        )

    def get_or_build(
        self,
        series: DicomSeriesRecord,
        phase_identifier: int | None = None,
    ) -> DicomVolume:
        fingerprint = series_fingerprint(series)
        cached = self.get_volume(
            series.series_instance_uid,
            phase_identifier,
        )
        if cached is not None and cached.fingerprint == fingerprint:
            logger.debug(
                "Using cached volume: series_uid=%s phase=%s",
                series.series_instance_uid,
                phase_identifier,
            )
            return cached

        instances = series.instances
        if phase_identifier is not None:
            phase = series.phase_by_identifier(phase_identifier)
            if phase is None:
                raise VolumeBuildError(
                    "Unknown temporal phase: "
                    f"series_uid={series.series_instance_uid} "
                    f"phase={phase_identifier}"
                )
            instances = phase.instances

        logger.info(
            "Building volume: series_uid=%s phase=%s instances=%d",
            series.series_instance_uid,
            phase_identifier,
            len(instances),
        )

        volume = self._build_volume(series, instances=instances)
        volume.fingerprint = fingerprint
        self._volumes_by_series_uid[
            (series.series_instance_uid, phase_identifier)
        ] = volume
        return volume

    # DICOM instances
    #     → 解码 PixelData
    #     → Slope / Intercept 转换为模态值
    #     → 根据空间位置排序
    #     → 校验矩阵、间距和方向
    #     → stack 为 (slice, row, column)
    #     → 建立体素坐标到患者物理坐标的映射
    #     → 提取 Axial / Coronal / Sagittal

    @staticmethod
    def _validate_instances(instances:tuple[DicomInstanceMeta,...]):
        if len(instances) < 2:
            raise VolumeBuildError(
                "MPR requires at least two DICOM instances"
            )

        first = instances[0]

        if first.rows is None or first.columns is None:
            raise VolumeBuildError(
                "DICOM Rows or Columns is missing"
            )

        if first.pixel_spacing is None:
            raise VolumeBuildError(
                "DICOM PixelSpacing is missing"
            )

        if first.image_orientation_patient is None:
            raise VolumeBuildError(
                "DICOM ImageOrientationPatient is missing"
            )


    def _build_volume(
        self,
        series: DicomSeriesRecord,
        *,
        instances: tuple[DicomInstanceMeta, ...] | None = None,
    ) -> DicomVolume:
        instances = series.instances if instances is None else instances
        self._validate_instances(instances=instances)
        from qt_dicom_viewer.core.volume_view import validate_volume_series
        from qt_dicom_viewer.core.pet import validate_pet_2d_series
        validate_volume_series(series)
        validate_pet_2d_series(series)
        if len({i.frame_of_reference_uid for i in instances}) != 1:
            raise VolumeBuildError("同一序列的 FrameOfReferenceUID 不一致")
        first = instances[0]


        orientation = np.asarray(
            first.image_orientation_patient,
            dtype=np.float64,
        )

        # DICOM IOP 前三项是列索引增加方向，后三项是行索引增加方向。
        column_index_direction = self._normalize(orientation[:3])
        row_index_direction = self._normalize(orientation[3:])

        slice_index_direction = self._normalize(
            np.cross(column_index_direction, row_index_direction)
        )

        positioned_instances: list[
            tuple[float, DicomInstanceMeta]
        ] = []

        for instance in instances:
            self._validate_instance_geometry(
                instance=instance,
                rows=first.rows,
                columns=first.columns,
                row_spacing=first.pixel_spacing.row,
                column_spacing=first.pixel_spacing.column,
                orientation=orientation,
            )

            position = np.asarray(
                instance.image_position_patient,
                dtype=np.float64,
            )

            # 将切片位置投影到切片法向量上。
            spatial_position = float(
                np.dot(position, slice_index_direction)
            )

            positioned_instances.append(
                (spatial_position, instance)
            )

        positioned_instances.sort(
            key=lambda item: item[0]
        )

        spatial_positions = np.asarray(
            [
                position
                for position, _ in positioned_instances
            ],
            dtype=np.float64,
        )

        position_differences = np.diff(spatial_positions)

        if np.any(np.abs(position_differences) < 1e-6):
            raise VolumeBuildError(
                "Series contains duplicate slice positions"
            )

        slice_spacing = float(
            np.median(np.abs(position_differences))
        )

        if slice_spacing <= 0:
            raise VolumeBuildError(
                "Invalid slice spacing"
            )

        frames: list[np.ndarray] = []
        source_frames: list[np.ndarray] = []
        value_metas: list[PixelValueMeta] = []
        source_meta = None
        reference_dataset = None
        loader = DicomLoader()
        default_window: WindowLevel | None = None
        representative_meta: InstanceDisplayMeta | None = None

        for _, instance in positioned_instances:
            dataset = pydicom.dcmread(instance.path)
            modality_pixels = loader.to_modality_pixels(dataset)

            if modality_pixels.ndim != 2:
                raise VolumeBuildError(
                    f"Only single-frame 2D instances are currently "
                    f"supported: path={instance.path}"
                )

            if modality_pixels.shape != (first.rows, first.columns):
                raise VolumeBuildError(
                    f"Inconsistent pixel matrix: path={instance.path} "
                    f"shape={modality_pixels.shape}"
                )

            source_frames.append(modality_pixels)
            display_pixels, value_meta, value_scale = loader.to_display_values(dataset, modality_pixels)
            value_metas.append(value_meta)
            if reference_dataset is None:
                reference_dataset = dataset
                if series.modality.upper() == "PT":
                    _, source_meta, _ = loader.to_display_values(dataset, modality_pixels, preferred_unit="source")
            if default_window is None:
                default_window = loader.resolve_window(
                    dataset=dataset,
                    target_window=None,
                    modality_pixels=display_pixels,
                    pixel_value_meta=value_meta,
                    value_scale=value_scale,
                )
                representative_meta = loader.extract_instance_meta(
                    dataset
                )

            frames.append(display_pixels)

        value_meta = value_metas[0]
        if series.modality.upper() == "PT":
            if len({m.source_unit for m in value_metas}) != 1:
                raise VolumeBuildError("PET 体积中存在不同源 Units，无法构建统一定量域")
            if value_meta.source_unit == "BQML":
                warning = next((m.warning for m in value_metas if m.quantification == "unavailable"), None)
                if warning:
                    options = tuple(replace(o, available=False, warning=warning)
                                    if o.unit_id == "suvbw" else o
                                    for o in source_meta.unit_options)
                    source_meta = replace(source_meta, unit="Bq/ml", unit_id="source",
                                          scale_from_source=1.0, suv_type=None,
                                          quantification="unavailable", warning=warning,
                                          unit_options=options)
                    value_meta = source_meta
                    frames = source_frames
                    default_window = loader.resolve_window(reference_dataset, None, frames[0], value_meta)
                elif not np.allclose([m.scale_from_source for m in value_metas], value_meta.scale_from_source,
                                     rtol=1e-6, atol=0):
                    warning = "各切片 SUV 换算比例不同；显示上限按初始参考切片换算，切换单位后局部亮度可能变化"
                    value_meta = replace(value_meta, warning=warning)
                    source_meta = replace(source_meta, warning=warning)
            elif len({(m.unit, m.suv_type) for m in value_metas}) != 1:
                raise VolumeBuildError("PET SUV 类型在同一体积中不一致")

        # 体数据轴顺序：(slice, row, column)
        volume_pixels = np.ascontiguousarray(
            np.stack(frames, axis=0),
            dtype=np.float32,
        )

        first_ordered_instance = positioned_instances[0][1]
        origin = first_ordered_instance.image_position_patient

        if origin is None:
            raise VolumeBuildError(
                "First ordered instance has no position"
            )

        if default_window is None or representative_meta is None:
            raise VolumeBuildError(
                "Could not determine the volume display metadata"
            )

        return DicomVolume(
            modality_pixels=volume_pixels,
            geometry=VolumeGeometry(
                slice_count=volume_pixels.shape[0],
                rows=volume_pixels.shape[1],
                columns=volume_pixels.shape[2],
                row_spacing=first.pixel_spacing.row,
                column_spacing=first.pixel_spacing.column,
                slice_spacing=slice_spacing,
                origin_patient=origin,
                slice_index_direction_patient=self._to_vector3(
                    slice_index_direction
                ),
                row_index_direction_patient=self._to_vector3(
                    row_index_direction
                ),
                column_index_direction_patient=self._to_vector3(
                    column_index_direction
                ),
            ),
            series_uid=series.series_instance_uid,
            default_window=default_window,
            representative_instance_meta=representative_meta,
            suv_pixels=volume_pixels if value_meta.is_suv else None,
            suv_value_meta=value_meta if value_meta.is_suv else None,
            pixel_value_meta=value_meta,
            source_pixels=(np.ascontiguousarray(np.stack(source_frames), dtype=np.float32)
                           if value_meta.source_unit == "BQML" else None),
            source_value_meta=source_meta,
        )

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        length = float(np.linalg.norm(vector))

        if length <= 1e-8:
            raise VolumeBuildError(
                "Invalid zero-length direction vector"
            )

        return vector / length

    @staticmethod
    def _to_vector3(
            vector: np.ndarray,
    ) -> tuple[float, float, float]:
        if vector.shape != (3,):
            raise ValueError(
                f"Expected a 3D vector, got shape={vector.shape}"
            )

        return (
            float(vector[0]),
            float(vector[1]),
            float(vector[2]),
        )

    @staticmethod
    def _validate_instance_geometry(
        instance: DicomInstanceMeta,
        rows: int,
        columns: int,
        row_spacing: float,
        column_spacing: float,
        orientation: np.ndarray,
    ) -> None:
        if instance.rows != rows or instance.columns != columns:
            raise VolumeBuildError(
                f"Inconsistent Rows/Columns: path={instance.path}"
            )

        if instance.pixel_spacing is None:
            raise VolumeBuildError(
                f"Missing PixelSpacing: path={instance.path}"
            )

        if not np.allclose(
            [
                instance.pixel_spacing.row,
                instance.pixel_spacing.column,
            ],
            [row_spacing, column_spacing],
            rtol=1e-4,
            atol=1e-5,
        ):
            raise VolumeBuildError(
                f"Inconsistent PixelSpacing: path={instance.path}"
            )

        if instance.image_orientation_patient is None:
            raise VolumeBuildError(
                f"Missing ImageOrientationPatient: "
                f"path={instance.path}"
            )

        if not np.allclose(
            instance.image_orientation_patient,
            orientation,
            rtol=1e-4,
            atol=1e-5,
        ):
            raise VolumeBuildError(
                f"Inconsistent ImageOrientationPatient: "
                f"path={instance.path}"
            )

        if instance.image_position_patient is None:
            raise VolumeBuildError(
                f"Missing ImagePositionPatient: "
                f"path={instance.path}"
            )


def series_fingerprint(series: DicomSeriesRecord) -> str:
    entries = []
    for item in series.instances:
        stat = item.path.stat()
        entries.append((item.sop_instance_uid, item.image_position_patient,
                        item.image_orientation_patient, item.rows, item.columns,
                        item.pixel_spacing, item.frame_of_reference_uid,
                        str(item.path), stat.st_size, stat.st_mtime_ns))
    return sha256(repr(entries).encode()).hexdigest()
