import math
from dataclasses import dataclass, replace
from uuid import uuid4

from qt_dicom_viewer.model import Point, DragUpdateEvent, PointerPosition, ImagePoint
from qt_dicom_viewer.model.interaction import InteractionResult, OperationStartContext, \
    MeasureContext
from qt_dicom_viewer.model.measure import LengthMeasurementDraft, LengthMeasurement
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation


class LengthMeasureOperation(DragOperation):
    def __init__(
            self,
    ) -> None:
        self._recent_measurement: LengthMeasurementDraft | None = None
        self._context: MeasureContext | None = None

    def begin(self, position: PointerPosition, context: OperationStartContext | None) -> InteractionResult | None:
        if not isinstance(context, MeasureContext):
            raise TypeError("operation required right Context")
        point = position.image
        self._context = context
        if point is not None:
            self._recent_measurement = LengthMeasurementDraft(
                measurement_id=str(uuid4()),
                series_uid=context.series_uid,
                sop_instance_uid=context.sop_instance_uid,
                slice_index=0,
                start=point,
                end=point,
                length_mm=0.0,
            )
            return self._recent_measurement
        return None

    def update(self, drag_event: DragUpdateEvent) -> InteractionResult | None:
        draft = self._recent_measurement
        image_point = drag_event.current_position.image

        if draft is None or image_point is None:
            return None

        draft.end = image_point
        if self._context is not None:
           length = calculate_length_mm(
                start=draft.start,
                end=image_point,
                row_spacing= self._context.geometry.pixel_spacing.row,
                column_spacing = self._context.geometry.pixel_spacing.column,
            )
           draft.length_mm =  0 if length is None else length
           return draft
        return None

    def end(self,  position: PointerPosition) -> InteractionResult | None:
        draft = self._recent_measurement

        if draft is None:
            return None

        # 如果在图像范围外松开，使用最后一个有效终点。
        end_point = position.image or draft.end

        result = LengthMeasurement(
            measurement_id=draft.measurement_id,
            series_uid=draft.series_uid,
            sop_instance_uid=draft.sop_instance_uid,
            slice_index=draft.slice_index,
            start=draft.start,
            end=end_point,
            length_mm=draft.length_mm,
        )

        self._recent_measurement = None
        return result


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