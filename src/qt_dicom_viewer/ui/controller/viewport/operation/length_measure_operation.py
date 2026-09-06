import math
from dataclasses import replace
from uuid import uuid4

from qt_dicom_viewer.core.geometry_2d import (
    image_point_distance_mm,
)
from qt_dicom_viewer.core.measurement_geometry import edited_points
from qt_dicom_viewer.model import DragUpdateEvent, ImagePoint
from qt_dicom_viewer.model.measure import (
    LengthMeasurement,
    LengthMeasurementDraft,
    MeasureContext,
    MeasurementKind,
    MeasurementEditTarget,
)


class LengthMeasureOperation:
    """长度测量的无状态几何操作。"""

    def create_draft(
        self,
        *,
        point: ImagePoint,
        context: MeasureContext,
    ) -> LengthMeasurementDraft:
        return LengthMeasurementDraft(
            measurement_id=str(uuid4()),
            series_uid=context.series_uid,
            sop_instance_uid=context.sop_instance_uid,
            slice_index=context.slice_index,
            points=[point, point],
            length_mm=0.0,
            kind=context.measurement_kind,
        )

    def create_edit_draft(
        self,
        measurement: LengthMeasurement,
    ) -> LengthMeasurementDraft:
        return LengthMeasurementDraft(
            measurement_id=measurement.measurement_id,
            series_uid=measurement.series_uid,
            sop_instance_uid=measurement.sop_instance_uid,
            slice_index=measurement.slice_index,
            points=list(measurement.points),
            length_mm=measurement.length_mm,
            kind=measurement.kind,
        )

    def update_draft(
        self,
        *,
        draft: LengthMeasurementDraft,
        target: MeasurementEditTarget,
        drag_event: DragUpdateEvent,
        context: MeasureContext,
    ) -> LengthMeasurementDraft:
        image_point = drag_event.current_position.image

        if image_point is None:
            return draft

        points = edited_points(draft.points, target, drag_event)

        spacing = context.geometry.pixel_spacing
        length = image_point_distance_mm(
            first=points[0],
            second=points[1],
            row_spacing=spacing.row,
            column_spacing=spacing.column,
        )

        return replace(
            draft,
            points=points,
            length_mm=0.0 if length is None else length,
        )

    @staticmethod
    def commit(
        draft: LengthMeasurementDraft,
    ) -> LengthMeasurement:
        return LengthMeasurement(
            measurement_id=draft.measurement_id,
            series_uid=draft.series_uid,
            sop_instance_uid=draft.sop_instance_uid,
            slice_index=draft.slice_index,
            points=tuple(draft.points),
            length_mm=draft.length_mm,
            kind=draft.kind,
        )

    @staticmethod
    def is_valid(
        measurement: LengthMeasurement,
    ) -> bool:
        if measurement.kind == MeasurementKind.ARROW:
            a, b = measurement.points
            return math.hypot(a.column - b.column, a.row - b.row) >= 1
        return (
            math.isfinite(measurement.length_mm)
            and measurement.length_mm >= 1.0
        )
