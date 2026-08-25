from qt_dicom_viewer.model import SeriesDisplayMeta, FrameDisplayMeta, ViewportState, ViewportConfig
from qt_dicom_viewer.utils.utils import _display_text, _display_number


class OverlayPresenter:
    def build(
        self,
        *,
        viewport_config: ViewportConfig,
        series: SeriesDisplayMeta,
        frame: FrameDisplayMeta | None,
        state: ViewportState,
    ) -> dict:
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
            "viewType": _display_text(viewport_config.viewport_type),
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
                frame.window.center if frame else None, 0
            ),
            "windowWidth": _display_number(
                frame.window.width * (-1 if frame.inverted else 1) if frame else None, 0
            ),
            "zoom": f"{state.zoom * 100:.0f}%",
        }