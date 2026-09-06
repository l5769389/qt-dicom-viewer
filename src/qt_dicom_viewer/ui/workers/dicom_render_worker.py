import logging
from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import replace

import numpy as np
import pydicom
from PySide6.QtCore import QObject, Signal, Slot

from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.core.mpr_reslicer import MprReslicer
from qt_dicom_viewer.core.pseudocolor import apply_color_map
from qt_dicom_viewer.core.pet import validate_pet_2d_series
from qt_dicom_viewer.model import (
    FrameDisplayMeta,
    ImageGeometryMeta,
    InstanceDisplayMeta,
    MprFrame,
    MontageRenderRequest,
    MontageRenderResult,
    PixelSpacing,
    PixelValueMeta,
    MprRenderRequest,
    RenderFailure,
    RenderRequest,
    RenderResult,
    StackRenderRequest,
    WindowLevel,
)
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.model.render_models import MprRenderResult, StackRenderResult
from qt_dicom_viewer.model.render_models import VolumeLoadRequest, VolumeLoadResult
from qt_dicom_viewer.core.volume_view import validate_volume_series
from qt_dicom_viewer.core.pet_reconstruction import PetReconstructor
from qt_dicom_viewer.model.render_models import PetBatchRenderRequest

logger = logging.getLogger(__name__)

MONTAGE_CACHE_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class _CachedMontageFrame:
    modality_pixels: np.ndarray
    default_window: WindowLevel
    instance_meta: InstanceDisplayMeta


class _MontageFrameCache:
    """Worker-thread-only, byte-bounded cache of decoded modality frames."""

    def __init__(self, maximum_bytes: int = MONTAGE_CACHE_BYTES) -> None:
        self._maximum_bytes = max(0, int(maximum_bytes))
        self._total_bytes = 0
        self._items: OrderedDict[
            tuple[str, int], _CachedMontageFrame
        ] = OrderedDict()

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    def get(self, key: tuple[str, int]) -> _CachedMontageFrame | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def put(
        self,
        key: tuple[str, int],
        value: _CachedMontageFrame,
    ) -> None:
        byte_count = int(value.modality_pixels.nbytes)
        previous = self._items.pop(key, None)
        if previous is not None:
            self._total_bytes -= int(previous.modality_pixels.nbytes)

        # A single frame larger than the budget is still renderable; it simply
        # is not retained after this request.
        if byte_count > self._maximum_bytes:
            return

        self._items[key] = value
        self._total_bytes += byte_count
        while self._total_bytes > self._maximum_bytes and self._items:
            _, evicted = self._items.popitem(last=False)
            self._total_bytes -= int(evicted.modality_pixels.nbytes)

class DicomRenderWorker(QObject):
    render_finished = Signal(object)
    render_failed = Signal(object)

    def __init__(self,
                 series_catalog: SeriesCatalog,
                 volume_manager: VolumeManager,
                 ):
        super().__init__()
        self.series_catalog = series_catalog
        self._volume_manager = volume_manager
        self._mpr_reslicer = MprReslicer()
        self._montage_cache = _MontageFrameCache()
        self._stack_loader = DicomLoader()
        self._pet_reconstructor = PetReconstructor(series_catalog, volume_manager)

    @Slot(object)
    def handleRenderRequest(self, request: RenderRequest):
        logger.debug(f"worker received:{request.request_id}")

        try:
            if isinstance(request, PetBatchRenderRequest):
                self.render_finished.emit(self._pet_reconstructor.render(request))
            elif isinstance(request, StackRenderRequest):
                self._handle_stack_request(request)
            elif isinstance(request, MontageRenderRequest):
                self._handle_montage_request(request)
            elif isinstance(request, MprRenderRequest):
                self._handle_plane_request(request)
            elif isinstance(request, VolumeLoadRequest):
                series = self.series_catalog.get_series(request.series_uid)
                if series is None:
                    raise LookupError("找不到该序列")
                if getattr(series, "modality", "").upper() == "PT":
                    raise ValueError(
                        "暂不支持 PET 体绘制，请使用 PET 2D 或 MPR"
                    )
                validate_volume_series(series)
                volume = self._volume_manager.get_or_build(series)
                self.render_finished.emit(VolumeLoadResult(
                    response_id=request.request_id, viewport_id=request.viewport_id,
                    series_uid=request.series_uid, volume=volume,
                ))
            else:
                raise ValueError(
                    "Unsupported render request: "
                    f"{type(request)!r}"
                )
        except Exception as error:
            logger.exception(
                "Render failed: request_id=%s viewport_id=%s",
                request.request_id,
                request.viewport_id,
            )
            self.render_failed.emit(
                RenderFailure(
                    request_id=request.request_id,
                    viewport_id=request.viewport_id,
                    error=error,
                )
            )

    def _handle_montage_request(
        self,
        request: MontageRenderRequest,
    ) -> None:
        series = self.series_catalog.get_series(request.series_uid)
        if series is None:
            raise LookupError(
                "Series not found: "
                f"series_uid={request.series_uid}"
            )

        instances = series.instances
        if not instances:
            raise LookupError(
                "Series has no renderable instances: "
                f"series_uid={request.series_uid}"
            )

        slice_index = min(max(0, request.slice_index), len(instances) - 1)
        instance = instances[slice_index]
        cache_key = (request.series_uid, slice_index)
        cached = self._montage_cache.get(cache_key)
        loader = DicomLoader()

        if cached is None:
            dataset = pydicom.dcmread(instance.path)
            modality_pixels = loader.to_modality_pixels(dataset)
            if modality_pixels.ndim != 2:
                raise ValueError(
                    "Montage rendering requires a single-frame 2D image, "
                    f"got shape={modality_pixels.shape}"
                )
            cached = _CachedMontageFrame(
                modality_pixels=np.ascontiguousarray(
                    modality_pixels,
                    dtype=np.float32,
                ),
                default_window=loader.resolve_window(dataset, None),
                instance_meta=loader.extract_instance_meta(dataset),
            )
            self._montage_cache.put(cache_key, cached)

        effective_window = loader.normalize_window(
            request.window or cached.default_window
        )
        image = loader.apply_window(
            modality_pixels=cached.modality_pixels,
            target_window=effective_window,
            inverted=request.inverted,
        )
        pixel_spacing = instance.pixel_spacing or PixelSpacing(
            row=1.0,
            column=1.0,
        )
        self.render_finished.emit(
            MontageRenderResult(
                response_id=request.request_id,
                series_uid=request.series_uid,
                viewport_id=request.viewport_id,
                view_type=request.view_type,
                slice_index=slice_index,
                image=image,
                # Montage never samples pixels or measures in the thumbnails.
                modality_pixel=None,
                frame_meta=FrameDisplayMeta(
                    slice_index=slice_index,
                    slice_count=len(instances),
                    window=effective_window,
                    instance_meta=cached.instance_meta,
                    inverted=request.inverted,
                    geometry=ImageGeometryMeta(
                        rows=instance.rows or image.shape[0],
                        columns=instance.columns or image.shape[1],
                        pixel_spacing=pixel_spacing,
                        image_position_patient=instance.image_position_patient,
                        image_orientation_patient=instance.image_orientation_patient,
                    ),
                ),
            )
        )

    def _handle_stack_request(
        self,
        request: StackRenderRequest,
    ) -> None:
        try:
            series = self.series_catalog.get_series(request.series_uid)
            if series is None:
                raise LookupError(
                    "Series not found: "
                    f"series_uid={request.series_uid}"
                )
            validate_pet_2d_series(series)

            instances = series.instances
            slice_count = len(instances)
            if slice_count == 0:
                raise LookupError(
                    "Series has no renderable instances: "
                    f"series_uid={request.series_uid}"
                )
            actual_slice_index = min(
                max(0, request.slice_index),
                slice_count - 1,
            )

            instance = instances[actual_slice_index]
            dicom_load_result = self._stack_loader.load_a_dicom(
                instance_path=instance.path,
                render_request=request,
            )
            if dicom_load_result is None:
                raise ValueError(
                    f"DICOM 文件读取失败：{instance.path.name}"
                )
            result = StackRenderResult(
                response_id=request.request_id,
                series_uid=request.series_uid,
                viewport_id=request.viewport_id,
                view_type=request.view_type,
                image=apply_color_map(dicom_load_result.image, request.color_map),
                modality_pixel=dicom_load_result.modality_pixel,
                frame_meta=FrameDisplayMeta(
                    slice_index=actual_slice_index,
                    slice_count=slice_count,
                    window=dicom_load_result.window,
                    instance_meta=dicom_load_result.instance_meta,
                    inverted=dicom_load_result.inverted,
                    geometry=ImageGeometryMeta(
                        rows=instance.rows or 0,
                        columns=instance.columns or 0,
                        pixel_spacing=instance.pixel_spacing,
                        image_position_patient=instance.image_position_patient,
                        image_orientation_patient=instance.image_orientation_patient,
                    ),
                    pixel_value_meta=dicom_load_result.pixel_value_meta,
                ),
            )
            self.render_finished.emit(result)
        except Exception as error:
            logger.exception(
                "Render failed: request_id=%s "
                "viewport_id=%s",
                request.request_id,
                request.viewport_id,
            )
            self.render_failed.emit(
                RenderFailure(
                    request_id=request.request_id,
                    viewport_id=request.viewport_id,
                    error=error,
                )
            )


    def _handle_plane_request(
        self,
        request: MprRenderRequest,
    ) -> None:
        series = self.series_catalog.get_series(request.series_uid)
        if series is None:
            raise LookupError(
                "Series not found: "
                f"series_uid={request.series_uid}"
            )

        volume = (
            self._volume_manager.get_or_build(series)
            if request.phase_identifier is None
            else self._volume_manager.get_or_build(
                series,
                phase_identifier=request.phase_identifier,
            )
        )
        volume = volume.in_unit(request.value_unit)
        resolved_frame = request.mpr_frame or MprFrame.standard_lps(
            volume.geometry.center_patient
        )
        view_grids = None
        grid_spec = request.mpr_grid
        if grid_spec is None:
            # 首次 MPR 请求同时生成三个视图的固定网格，
            # 由 TabController 保存并在后续旋转请求中复用。
            view_grids = self._mpr_reslicer.create_view_grids(
                volume,
                resolved_frame,
            )
            grid_spec = view_grids.for_plane(request.plane)
        mpr_slice = self._mpr_reslicer.reslice(
            volume=volume,
            plane=request.plane,
            frame=resolved_frame,
            view_roll_radians=request.view_roll_radians,
            grid_spec=grid_spec,
            grid_anchor=request.mpr_grid_anchor,
            projection_mode=request.projection_mode,
            slab_thickness_mm=request.slab_thickness_mm,
        )
        plane_pixels = mpr_slice.modality_pixels
        plane_geometry = mpr_slice.geometry
        pixel_spacing = PixelSpacing(
            row=plane_geometry.row_spacing,
            column=plane_geometry.column_spacing,
        )

        loader = DicomLoader()
        minimum = 0.01 if volume.pixel_value_meta.is_suv else 0.001 if getattr(series, "modality", "").upper() == "PT" else 1.
        effective_window = loader.normalize_window(
            request.window or volume.default_window, minimum_width=minimum
        )
        image = loader.apply_window(
            modality_pixels=plane_pixels,
            target_window=effective_window,
            inverted=request.inverted,
            minimum_width=minimum,
        )

        rows = plane_geometry.rows
        columns = plane_geometry.columns
        instance_meta = replace(
            volume.representative_instance_meta,
            instance_number=None,
            sop_instance_uid=None,
            rows=rows,
            columns=columns,
            pixel_spacing=(
                pixel_spacing.row,
                pixel_spacing.column,
            ),
            image_position=plane_geometry.image_origin_patient,
            slice_location=plane_geometry.navigation_position_patient,
        )
        self.render_finished.emit(
            MprRenderResult(
                response_id=request.request_id,
                series_uid=request.series_uid,
                viewport_id=request.viewport_id,
                view_type=request.view_type,
                image=apply_color_map(image, request.color_map),
                modality_pixel=np.ascontiguousarray(
                    plane_pixels,
                    dtype=np.float32,
                ),
                frame_meta=FrameDisplayMeta(
                    slice_index=mpr_slice.slice_index,
                    slice_count=mpr_slice.slice_count,
                    window=effective_window,
                    instance_meta=instance_meta,
                    inverted=request.inverted,
                    geometry=ImageGeometryMeta(
                        rows=rows,
                        columns=columns,
                        pixel_spacing=pixel_spacing,
                        image_position_patient=(
                            plane_geometry.image_origin_patient
                        ),
                        image_orientation_patient=(
                            plane_geometry.image_orientation_patient
                        ),
                    ),
                    pixel_value_meta=volume.pixel_value_meta,
                ),
                mpr_frame=plane_geometry.frame,
                plane_geometry=plane_geometry,
                phase_identifier=request.phase_identifier,
                mpr_view_grids=view_grids,
            )
        )

    def _handle_load_process(self, image_data) -> None:
        return  image_data
