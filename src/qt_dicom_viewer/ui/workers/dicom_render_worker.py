import logging
from dataclasses import replace

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.core.mpr_reslicer import MprReslicer
from qt_dicom_viewer.model import (
    FrameDisplayMeta,
    ImageGeometryMeta,
    MprFrame,
    PixelSpacing,
    MprRenderRequest,
    RenderFailure,
    RenderRequest,
    RenderResult,
    StackRenderRequest,
)
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.model.render_models import MprRenderResult, StackRenderResult
from qt_dicom_viewer.model.render_models import VolumeLoadRequest, VolumeLoadResult
from qt_dicom_viewer.core.volume_view import validate_volume_series

logger = logging.getLogger(__name__)

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

    @Slot(object)
    def handleRenderRequest(self, request: RenderRequest):
        logger.debug(f"worker received:{request.request_id}")

        try:
            if isinstance(request, StackRenderRequest):
                self._handle_stack_request(request)
            elif isinstance(request, MprRenderRequest):
                self._handle_plane_request(request)
            elif isinstance(request, VolumeLoadRequest):
                series = self.series_catalog.get_series(request.series_uid)
                if series is None:
                    raise LookupError("找不到该序列")
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
            dicom_load_result = DicomLoader().load_a_dicom(
                instance_path=instance.path,
                render_request=request,
            )
            if dicom_load_result is not None:
                result = StackRenderResult(
                    response_id=request.request_id,
                    series_uid=request.series_uid,
                    viewport_id=request.viewport_id,
                    view_type=request.view_type,
                    image=dicom_load_result.image,
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
        effective_window = loader.normalize_window(
            request.window or volume.default_window
        )
        image = loader.apply_window(
            modality_pixels=plane_pixels,
            target_window=effective_window,
            inverted=request.inverted,
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
                image=image,
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
                ),
                mpr_frame=plane_geometry.frame,
                plane_geometry=plane_geometry,
                phase_identifier=request.phase_identifier,
                mpr_view_grids=view_grids,
            )
        )

    def _handle_load_process(self, image_data) -> None:
        return  image_data
