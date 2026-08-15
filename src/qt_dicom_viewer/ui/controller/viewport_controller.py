import logging
import uuid
from dataclasses import replace
from math import isfinite

from PySide6.QtCore import QObject, Signal, Slot, Property

from qt_dicom_viewer.core.dicom_models import ViewportState, ViewportConfig, RenderRequest, RenderResult, \
    WindowLevel, FrameDisplayMeta

logger = logging.getLogger(__name__)


def _display_text(value: str | None) -> str:
    if value is None:
        return "--"
    text = str(value).strip()
    return text or "--"


def _display_number(value: float | int | None, precision: int = 2) -> str:
    if value is None:
        return "--"
    number = float(value)
    if not isfinite(number):
        return "--"
    if number.is_integer():
        return str(int(number))
    return f"{number:.{precision}f}".rstrip("0").rstrip(".")


class ViewportController(QObject):
    renderRequested = Signal(object)
    imageSourceChanged = Signal()
    overlayChanged = Signal()

    def __init__(self, viewport_config: ViewportConfig, parent = None):
        super().__init__(parent)
        self.viewport_config = viewport_config
        self.state = ViewportState()
        self._image_revision = 0
        self._has_image = False
        self._frame_meta: FrameDisplayMeta | None = None

    def request_first_loader(self) -> None:
        request = RenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            slice_index= 0,
            window= None
        )
        logger.debug(
            "Render started: request_id=%s viewport_id=%s",
            request.request_id,
            request.viewport_id,
        )
        self.renderRequested.emit(request)

    def request_render(self) -> None:
        request = RenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            slice_index=self.state.slice_index,
            window=None
        )
        logger.debug(
            "Render started: request_id=%s viewport_id=%s",
            request.request_id,
            request.viewport_id,
        )
        self.renderRequested.emit(request)

    @Slot(object)
    def handleRenderResult(self, result: RenderResult) -> None:
        if (
                result.viewport_id
                != self.viewport_config.viewport_id
        ):
            return
        self._frame_meta = result.frame_meta
        self.state = replace(
            self.state,
            slice_index=result.frame_meta.slice_index,
            slice_count=result.frame_meta.slice_count,
            window=result.frame_meta.window,
        )
        self.overlayChanged.emit()

        if result.image is None:
            return

        self._has_image = True
        self._image_revision += 1
        self.imageSourceChanged.emit()
        logger.debug(
            "Viewport image updated: "
            "viewport_id=%s revision=%d",
            result.viewport_id,
            self._image_revision,
        )


    @Property(str, notify=imageSourceChanged)
    def imageSource(self) -> str:
        if not self._has_image:
            return ""

        return (
            f"image://dicom/"
            f"{self.viewport_config.viewport_id}/"
            f"{self._image_revision}"
        )

    @Property("QVariantMap", notify=overlayChanged)
    def overlayInfo(self) -> dict:
        series = self.viewport_config.series_meta
        frame = self._frame_meta
        instance = frame.instance_meta if frame else None
        position = instance.image_position if instance else None
        spacing = instance.pixel_spacing if instance else None

        return {
            "patientName": _display_text(series.patient_name),
            "patientId": _display_text(series.patient_id),
            "studyDescription": _display_text(series.study_description),
            "seriesDescription": _display_text(series.series_description),
            "modality": _display_text(series.modality),
            "manufacturer": _display_text(
                instance.manufacturer if instance else None
            ),
            "kvp": _display_number(instance.kvp if instance else None),
            "tubeCurrentMa": _display_number(
                instance.tube_current_ma if instance else None
            ),
            "sliceThickness": _display_number(
                instance.slice_thickness if instance else None
            ),
            "sliceIndex": str(frame.slice_index + 1) if frame else "--",
            "sliceCount": str(frame.slice_count) if frame else "--",
            "instanceNumber": _display_number(
                instance.instance_number if instance else None,
                precision=0,
            ),
            "rows": _display_number(
                instance.rows if instance else None,
                precision=0,
            ),
            "columns": _display_number(
                instance.columns if instance else None,
                precision=0,
            ),
            # DICOM PixelSpacing 的顺序是 row(Y), column(X)。
            "pixelSpacingX": _display_number(spacing[1] if spacing else None),
            "pixelSpacingY": _display_number(spacing[0] if spacing else None),
            "positionX": _display_number(position[0] if position else None),
            "positionY": _display_number(position[1] if position else None),
            "positionZ": _display_number(position[2] if position else None),
            "sliceLocation": _display_number(
                instance.slice_location if instance else None
            ),
            "windowCenter": _display_number(
                frame.window.center if frame else None
            ),
            "windowWidth": _display_number(
                frame.window.width if frame else None
            ),
            "zoom": f"{self.state.zoom * 100:.0f}%",
            "cursorX": "--",
            "cursorY": "--",
            "pixelValue": "--",
        }
