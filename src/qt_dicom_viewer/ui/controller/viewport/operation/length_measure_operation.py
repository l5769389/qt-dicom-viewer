import math
from dataclasses import dataclass, replace
from uuid import uuid4

from qt_dicom_viewer.model import Point, DragUpdateEvent, PointerPosition
from qt_dicom_viewer.model.interaction import InteractionResult, OperationStartContext, \
    MeasureContext
from qt_dicom_viewer.model.measure import LengthMeasurementDraft, LengthMeasurement
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation


class LengthMeasureOperation(DragOperation):
    def __init__(
            self,
    ) -> None:
        self._recent_measurement: LengthMeasurementDraft | None = None

    def begin(self, position: PointerPosition, context: OperationStartContext | None) -> InteractionResult | None:
        if not isinstance(context, MeasureContext):
            raise TypeError("operation required right Context")
        point = position.image
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

    def update(self, drag_event: DragUpdateEvent) -> InteractionResult | None:
        draft = self._recent_measurement
        image_point = drag_event.current_position.image

        if draft is None or image_point is None:
            return None

        draft.end = image_point

        # 等 PixelSpacing 加入 MeasureContext 后再计算毫米值。
        # draft.length_mm = self._calculate_length(...)

        return draft

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
