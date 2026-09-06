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
        value_meta = frame.pixel_value_meta if frame else None
        window_precision = 2 if value_meta and value_meta.is_suv else 0
        pet_value_precision = (
            3
            if value_meta and value_meta.unit in {"SUVbw", "kBq/ml"}
            else 0
        )
        position = instance.image_position if instance else None
        spacing = instance.pixel_spacing if instance else None
        is_ct = series.modality.upper() == "CT"
        is_pet = series.modality.upper() == "PT"
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
            "kvp": (
                _display_number(instance.kvp if instance else None)
                if is_ct
                else ""
            ),
            "tubeCurrentMa": (
                _display_number(
                    instance.tube_current_ma if instance else None
                )
                if is_ct
                else ""
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
                frame.window.center if frame else None,
                window_precision,
            ),
            "windowWidth": _display_number(
                (
                    frame.window.width * (-1 if frame.inverted else 1)
                    if frame
                    else None
                ),
                window_precision,
            ),
            "zoom": f"{state.zoom * 100:.0f}%",
            "radiopharmaceutical": (
                instance.radiopharmaceutical or ""
                if instance
                else ""
            ),
            "petUnits": instance.pet_units or "" if instance else "",
            "suvType": (
                value_meta.suv_type or ""
                if value_meta
                else ""
            ),
            "pixelUnit": value_meta.unit if value_meta else "",
            "decayCorrection": (
                instance.decay_correction or ""
                if instance
                else ""
            ),
            "quantificationWarning": (
                value_meta.warning or ""
                if value_meta
                else ""
            ),
            "correctedImage": (
                "/".join(instance.corrected_image)
                if instance
                else ""
            ),
            "petDisplayLower": "0" if frame and is_pet else "",
            "petDisplayUpper": _display_number(
                (
                    state.window.center + state.window.width / 2.0
                    if state.window and is_pet
                    else None
                ),
                pet_value_precision,
            ),
            "rotation": _display_number(state.rotation_degrees, 0),
            "flip": (
                "H/V"
                if state.horizontal_flip and state.vertical_flip
                else "H"
                if state.horizontal_flip
                else "V"
                if state.vertical_flip
                else "--"
            ),
        }
