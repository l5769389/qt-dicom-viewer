from math import isfinite, sqrt
from typing import Sequence

from qt_dicom_viewer.model import (
    FrameDisplayMeta,
    MprPlane,
    SeriesDisplayMeta,
    ViewportConfig,
    ViewportState,
)
from qt_dicom_viewer.utils.utils import _display_text, _display_number


_MPR_PLANE_NAMES = {
    MprPlane.AXIAL: "Axial",
    MprPlane.CORONAL: "Coronal",
    MprPlane.SAGITTAL: "Sagittal",
}
_PLANE_NAMES_BY_AXIS = ("Sagittal", "Coronal", "Axial")
_POSITION_LABELS_BY_AXIS = (
    ("L", "R"),
    ("P", "A"),
    ("S", "I"),
)


def _format_view_position(
    viewport_type,
    image_position_patient: Sequence[float] | None,
    image_orientation_patient: Sequence[float] | None,
) -> str:
    """Format the plane's signed LPS distance like ``Axial, I: 12.34mm``."""
    if (
        image_position_patient is None
        or image_orientation_patient is None
        or len(image_position_patient) != 3
        or len(image_orientation_patient) != 6
    ):
        return ""

    position = tuple(float(value) for value in image_position_patient)
    orientation = tuple(
        float(value) for value in image_orientation_patient
    )
    if not all(isfinite(value) for value in (*position, *orientation)):
        return ""

    column = orientation[:3]
    row = orientation[3:]
    normal = (
        column[1] * row[2] - column[2] * row[1],
        column[2] * row[0] - column[0] * row[2],
        column[0] * row[1] - column[1] * row[0],
    )
    normal_length = sqrt(sum(value * value for value in normal))
    if normal_length <= 1e-12:
        return ""

    normal = tuple(value / normal_length for value in normal)
    dominant_axis = max(range(3), key=lambda index: abs(normal[index]))
    if normal[dominant_axis] < 0.0:
        normal = tuple(-value for value in normal)

    signed_distance = sum(
        position[index] * normal[index]
        for index in range(3)
    )
    positive_label, negative_label = _POSITION_LABELS_BY_AXIS[
        dominant_axis
    ]
    direction_label = (
        positive_label if signed_distance >= 0.0 else negative_label
    )
    plane_name = _MPR_PLANE_NAMES.get(
        viewport_type,
        _PLANE_NAMES_BY_AXIS[dominant_axis],
    )
    distance = 0.0 if abs(signed_distance) < 0.005 else abs(signed_distance)
    return f"{plane_name}, {direction_label}: {distance:.2f}mm"


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
        geometry = frame.geometry if frame else None
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
            "viewPosition": _format_view_position(
                viewport_config.viewport_type,
                geometry.image_position_patient if geometry else None,
                geometry.image_orientation_patient if geometry else None,
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
                frame.window.center if frame else None, 0
            ),
            "windowWidth": _display_number(
                frame.window.width * (-1 if frame.inverted else 1) if frame else None, 0
            ),
            "zoom": f"{state.zoom * 100:.0f}%",
        }
