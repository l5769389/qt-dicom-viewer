import logging

from PySide6.QtCore import QObject, Signal, Slot

from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.model import (
    FrameDisplayMeta,
    ImageGeometryMeta,
    RenderRequest,
    RenderResult,
)
from qt_dicom_viewer.application.series_catalog import SeriesCatalog

logger = logging.getLogger(__name__)

class DicomRenderWorker(QObject):
    render_finished = Signal(object)
    render_failed = Signal(object)

    def __init__(self,  series_catalog: SeriesCatalog):
        super().__init__()
        self.series_catalog = series_catalog

    @Slot(object)
    def handleRenderRequest(self,request: RenderRequest):
        logger.debug(f"worker received:{request.request_id}")
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
                result = RenderResult(
                    response_id=request.request_id,
                    series_uid=request.series_uid,
                    viewport_id=request.viewport_id,
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
            self.render_failed.emit(error)


    def _handle_load_process(self, image_data) -> None:
        return  image_data
