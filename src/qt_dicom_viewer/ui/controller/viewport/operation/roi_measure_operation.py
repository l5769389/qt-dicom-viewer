"""矩形和椭圆共用包围盒编辑，只在掩膜及面积计算时区分形状。"""

from dataclasses import replace
from uuid import uuid4

from qt_dicom_viewer.core.measurement_geometry import edited_points, roi_corners, roi_metrics
from qt_dicom_viewer.model.image_geometry import DragUpdateEvent, ImagePoint
from qt_dicom_viewer.model.measure import (
    EditTargetKind, MeasureContext, MeasurementEditTarget,
    RoiMeasurement, RoiMeasurementDraft, RoiMetrics,
)


class RoiMeasureOperation:
    def create_draft(self, *, point: ImagePoint, context: MeasureContext) -> RoiMeasurementDraft:
        return RoiMeasurementDraft(
            measurement_id=str(uuid4()), series_uid=context.series_uid,
            sop_instance_uid=context.sop_instance_uid, slice_index=context.slice_index,
            kind=context.measurement_kind, points=[point, point], metrics=RoiMetrics(unit=context.pixel_unit),
        )

    def create_edit_draft(self, measurement: RoiMeasurement) -> RoiMeasurementDraft:
        return RoiMeasurementDraft(
            measurement_id=measurement.measurement_id, series_uid=measurement.series_uid,
            sop_instance_uid=measurement.sop_instance_uid, slice_index=measurement.slice_index,
            kind=measurement.kind, points=list(measurement.points), metrics=measurement.metrics,
        )

    def update_draft(self, *, draft: RoiMeasurementDraft, target: MeasurementEditTarget,
                     drag_event: DragUpdateEvent, context: MeasureContext) -> RoiMeasurementDraft:
        point = drag_event.current_position.image
        if point is None:
            return draft
        if target.kind == EditTargetKind.CONTROL_POINT and target.index in range(4):
            opposite = roi_corners(draft.points)[(target.index + 2) % 4]
            points = [opposite, point]
        else:
            points = edited_points(draft.points, target, drag_event)
        spacing = context.geometry.pixel_spacing
        metrics = roi_metrics(points, draft.kind, context.modality_pixels,
                              row_spacing=spacing.row, column_spacing=spacing.column,
                              unit=context.pixel_unit)
        return replace(draft, points=points, metrics=metrics)

    @staticmethod
    def commit(draft: RoiMeasurementDraft) -> RoiMeasurement:
        return RoiMeasurement(
            measurement_id=draft.measurement_id, series_uid=draft.series_uid,
            sop_instance_uid=draft.sop_instance_uid, slice_index=draft.slice_index,
            kind=draft.kind, points=tuple(draft.points), metrics=draft.metrics,
        )

    @staticmethod
    def is_valid(measurement: RoiMeasurement) -> bool:
        # 允许轮廓超出影像；没有有效像素时仍可测面积，但灰度统计显示为空。
        first, second = measurement.points
        return (abs(first.column - second.column) >= 1e-3
                and abs(first.row - second.row) >= 1e-3
                and measurement.metrics.area_mm2 is not None
                and measurement.metrics.area_mm2 > 0)
