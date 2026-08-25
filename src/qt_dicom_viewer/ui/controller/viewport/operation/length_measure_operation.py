import math
from dataclasses import replace
from uuid import uuid4

from qt_dicom_viewer.model import DragUpdateEvent, ImagePoint
from qt_dicom_viewer.model.measure import (
    EditTargetKind,
    LengthMeasurement,
    LengthMeasurementDraft,
    MeasureContext,
    MeasurementEditTarget,
)


class LengthMeasureOperation:
    """Stateless geometry operations for length measurements."""

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

        points = draft.points.copy()

        if (
            target.kind == EditTargetKind.CONTROL_POINT
            and target.index is not None
            and 0 <= target.index < len(points)
        ):
            points[target.index] = image_point

        # Segment/body translation needs an image-space delta and will be
        # implemented with the corresponding edit strategy.

        spacing = context.geometry.pixel_spacing
        length = calculate_length_mm(
            start=points[0],
            end=points[1],
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
        )

    @staticmethod
    def is_valid(
        measurement: LengthMeasurement,
    ) -> bool:
        return (
            math.isfinite(measurement.length_mm)
            and measurement.length_mm >= 1.0
        )


def calculate_length_mm(
    start: ImagePoint,
    end: ImagePoint,
    *,
    row_spacing: float | None,
    column_spacing: float | None,
) -> float | None:
    if (
        row_spacing is None
        or column_spacing is None
        or not math.isfinite(row_spacing)
        or not math.isfinite(column_spacing)
        or row_spacing <= 0
        or column_spacing <= 0
    ):
        return None

    delta_column_mm = (
        end.column - start.column
    ) * column_spacing
    delta_row_mm = (
        end.row - start.row
    ) * row_spacing

    return math.hypot(
        delta_column_mm,
        delta_row_mm,
    )
