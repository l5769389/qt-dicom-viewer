"""统一管理测量创建、编辑、选中及切面隔离，几何计算交给无状态操作。"""

import math
from dataclasses import asdict, replace

from PySide6.QtCore import QObject, Property, Signal, Slot

from qt_dicom_viewer.core.geometry_2d import point_distance
from qt_dicom_viewer.core.measurement_hit_test import (
    hit_test_control_points,
    hit_test_interior,
    hit_test_label,
    hit_test_outline,
    nearest_hit,
)
from qt_dicom_viewer.model import DragUpdateEvent, ImagePoint, Offset, Point, PointerPosition
from qt_dicom_viewer.model.dicom_types import FrameDisplayMeta
from qt_dicom_viewer.model.measure import (
    AngleMeasurement, AngleMeasurementDraft, AnglePointIndex,
    CreateMeasurementTransaction, EditMeasurementTransaction, EditTargetKind,
    LengthMeasurement, LengthMeasurementDraft, MeasureContext, Measurement,
    MeasurementDraft, MeasurementEditTarget, MeasurementHit, MeasurementKind,
    MeasurementLabelRegion, MeasurementTransaction, RoiMeasurement, RoiMeasurementDraft,
)
from qt_dicom_viewer.ui.controller.viewport.operation.angle_measure_operation import AngleMeasureOperation
from qt_dicom_viewer.ui.controller.viewport.operation.length_measure_operation import LengthMeasureOperation
from qt_dicom_viewer.ui.controller.viewport.operation.roi_measure_operation import RoiMeasureOperation


class MeasurementController(QObject):
    measurementsChanged = Signal()
    activeTransactionChanged = Signal()
    selectionChanged = Signal()
    hoverChanged = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._measurements: dict[str, Measurement] = {}
        self._active_transaction: MeasurementTransaction | None = None
        self._selected_measurement_id: str | None = None
        self._hover_hit: MeasurementHit | None = None
        self._length_operation = LengthMeasureOperation()
        self._angle_operation = AngleMeasureOperation()
        self._roi_operation = RoiMeasureOperation()
        self._drag_reference: MeasurementDraft | None = None
        self._drag_start: PointerPosition | None = None
        self._frame_key: tuple | None = None
        self._measurement_frames: dict[str, tuple | None] = {}
        self._visible_slice: int | None = None
        self._label_regions: dict[str, MeasurementLabelRegion] = {}
        # 标签布局来自 QML；模型增删、编辑或切面变化后，等待下次输入前重新提供。
        self.measurementsChanged.connect(self._label_regions.clear)
        self.measurementsChanged.connect(self.clearHover)
        self.activeTransactionChanged.connect(self.clearHover)
        # 选择变化会改变光标语义，但不改变“鼠标命中了哪个部位”这一事实。
        self.selectionChanged.connect(self.hoverChanged.emit)

    def set_frame(self, series_uid: str, frame: FrameDisplayMeta) -> None:
        """MPR 的索引不足以识别切面；同时比较采样原点、方向、尺寸和间距。"""
        geometry = frame.geometry
        pose = (geometry.pixel_spacing.row, geometry.pixel_spacing.column,
                *(geometry.image_position_patient or ()),
                *(geometry.image_orientation_patient or ()))
        key = (series_uid, frame.instance_meta.sop_instance_uid, frame.slice_index,
               geometry.rows, geometry.columns, tuple(round(v, 7) for v in pose))
        if key == self._frame_key and self._visible_slice == frame.slice_index:
            return
        self.cancel_transaction()
        self.clear_selection()
        self._frame_key = key
        self._visible_slice = frame.slice_index
        self.measurementsChanged.emit()

    def set_current_slice(self, index: int) -> None:
        self.cancel_transaction()
        self.clear_selection()
        self._visible_slice = index
        self.measurementsChanged.emit()

    def _visible(self, measurement: Measurement) -> bool:
        return ((self._visible_slice is None or measurement.slice_index == self._visible_slice)
                and self._measurement_frames.get(measurement.measurement_id) == self._frame_key)

    @Property("QVariantList", notify=measurementsChanged)
    def measurementItems(self) -> list[dict]:
        editing_id = (self._active_transaction.draft.measurement_id
                      if isinstance(self._active_transaction, EditMeasurementTransaction) else None)
        return [self._to_qml_item(m) for key, m in self._measurements.items()
                if key != editing_id and self._visible(m)]

    @Property("QVariantMap", notify=activeTransactionChanged)
    def activeTransaction(self) -> dict:
        transaction = self._active_transaction
        if transaction is None:
            return {}
        item = self._to_qml_item(transaction.draft)
        item["editTarget"] = {"kind": transaction.target.kind.value, "index": transaction.target.index}
        if self._creating_angle() and transaction.target.index == AnglePointIndex.VERTEX:
            item["label"] = "选择顶点"
        return item

    @Property(str, notify=activeTransactionChanged)
    def instruction(self) -> str:
        if self._creating_angle():
            return ("选择顶点 · Esc 取消" if self._active_transaction.target.index == AnglePointIndex.VERTEX
                    else "选择终点完成角度 · Esc 取消")
        return ""

    @Property(str, notify=selectionChanged)
    def selectedMeasurementId(self) -> str:
        return self._selected_measurement_id or ""

    @Property("QVariantMap", notify=hoverChanged)
    def hoverHit(self) -> dict:
        hit = self._hover_hit
        if hit is None:
            return {}
        return {"measurementId": hit.measurement_id,
                "kind": hit.target.kind.value, "index": hit.target.index}

    @Property(str, notify=hoverChanged)
    def hoverCursorKind(self) -> str:
        """仅选中图形的可整体移动部位显示移动图标，控制点保持调整形状的语义。"""
        hit = self._hover_hit
        if (hit is not None and not self.has_active_transaction
                and hit.measurement_id == self._selected_measurement_id
                and hit.target.kind in (EditTargetKind.OUTLINE, EditTargetKind.INTERIOR, EditTargetKind.LABEL)):
            return "pan"
        return ""

    def update_hover(self, point: ImagePoint | None, *, slice_index: int,
                     endpoint_tolerance: float, line_tolerance: float,
                     viewport_point: Point | None = None) -> None:
        """悬停只判断命中，不改变选择、不修改图形，也不计算像素统计。"""
        hit = None
        if point is not None and not self.has_active_transaction:
            hit = self.hit_test(point, slice_index=slice_index,
                                endpoint_tolerance=endpoint_tolerance, line_tolerance=line_tolerance,
                                viewport_point=viewport_point)
        # 光标只关心部位和所属图形；沿同一轮廓移动时无需因距离变化反复通知 QML。
        before = (self._hover_hit.measurement_id, self._hover_hit.target) if self._hover_hit else None
        after = (hit.measurement_id, hit.target) if hit else None
        self._hover_hit = hit
        if before != after:
            self.hoverChanged.emit()

    @Slot()
    def clearHover(self) -> None:
        if self._hover_hit is not None:
            self._hover_hit = None
            self.hoverChanged.emit()

    @property
    def has_active_transaction(self) -> bool:
        return self._active_transaction is not None

    @staticmethod
    def _to_qml_item(measurement: Measurement | MeasurementDraft) -> dict:
        item = {"measurementId": measurement.measurement_id,
                "points": [{"column": p.column, "row": p.row} for p in measurement.points]}
        if isinstance(measurement, (LengthMeasurement, LengthMeasurementDraft)):
            item.update(type="length", startColumn=measurement.points[0].column,
                        startRow=measurement.points[0].row, endColumn=measurement.points[1].column,
                        endRow=measurement.points[1].row, label=f"{measurement.length_mm:.1f} mm")
        elif isinstance(measurement, (AngleMeasurement, AngleMeasurementDraft)):
            label = f"{measurement.angle:.1f}°" if math.isfinite(measurement.angle) else "—°"
            item.update(type="angle", label=label)
        else:
            item.update(type=measurement.kind.value, metrics=asdict(measurement.metrics),
                        label="矩形 ROI" if measurement.kind == MeasurementKind.RECT else "椭圆 ROI")
        return item

    def _operation(self, measurement: Measurement | MeasurementDraft):
        if isinstance(measurement, (LengthMeasurement, LengthMeasurementDraft)):
            return self._length_operation
        if isinstance(measurement, (AngleMeasurement, AngleMeasurementDraft)):
            return self._angle_operation
        return self._roi_operation

    def _creating_angle(self) -> bool:
        return (isinstance(self._active_transaction, CreateMeasurementTransaction)
                and isinstance(self._active_transaction.draft, AngleMeasurementDraft))

    def tap_at(self, point: ImagePoint | None, *, slice_index: int,
               endpoint_tolerance: float, line_tolerance: float,
               context: MeasureContext | None = None,
               viewport_point: Point | None = None) -> None:
        if point is not None and self._creating_angle():
            self._update_point(point)
            self._advance_angle_or_commit()
            return
        if self._active_transaction is not None:
            self.cancel_transaction()
        hit = (self.hit_test(point, slice_index=slice_index,
                            endpoint_tolerance=endpoint_tolerance, line_tolerance=line_tolerance,
                            viewport_point=viewport_point)
               if point is not None else None)
        if hit is None and point is not None and context is not None and context.measurement_kind == MeasurementKind.ANGLE:
            self._begin_create_transaction(point=point, context=context)
        elif hit is not None:
            self.select(hit)
        else:
            self.clear_selection()

    def preview_at(self, point: ImagePoint | None) -> None:
        """角度两段之间的悬停只更新草稿；按住鼠标时仍由拖动事件负责。"""
        if self._creating_angle() and self._drag_reference is None and point is not None:
            self._update_point(point)

    def begin(self, position: PointerPosition, context: MeasureContext | None) -> None:
        if not isinstance(context, MeasureContext):
            raise TypeError("MeasurementController requires MeasureContext")
        point = position.image
        if point is None:
            return
        if not (self._creating_angle() and context.measurement_kind == MeasurementKind.ANGLE):
            self.cancel_transaction()
            hit = self.hit_test(point, slice_index=context.slice_index,
                                endpoint_tolerance=context.endpoint_tolerance,
                                line_tolerance=context.line_tolerance,
                                viewport_point=position.viewport)
            if hit is None:
                self._begin_create_transaction(point=point, context=context)
            else:
                self._begin_edit_transaction(hit=hit, context=context)
        if self._active_transaction is not None:
            self._drag_reference = replace(self._active_transaction.draft,
                                           points=list(self._active_transaction.draft.points))
            self._drag_start = position

    def update(self, drag_event: DragUpdateEvent) -> None:
        transaction = self._active_transaction
        if transaction is None:
            return
        transaction.draft = self._operation(transaction.draft).update_draft(
            draft=self._drag_reference or transaction.draft,
            target=transaction.target, drag_event=drag_event, context=transaction.context,
        )
        if self._creating_angle() and transaction.target.index == AnglePointIndex.VERTEX:
            transaction.draft.points[2] = transaction.draft.points[1]
        self.activeTransactionChanged.emit()

    def _update_point(self, point: ImagePoint) -> None:
        position = PointerPosition(Point(point.column, point.row), point)
        self.update(DragUpdateEvent(self._drag_start or position, position, Offset(0, 0), Offset(0, 0)))

    def end(self, position: PointerPosition) -> None:
        if self._active_transaction is None:
            return
        # 松开位置可能比最后一次 move 更新，必须采纳 release 的坐标。
        if position.image is not None:
            self._update_point(position.image)
        self._drag_reference = None
        self._drag_start = None
        self._advance_angle_or_commit()

    def _advance_angle_or_commit(self) -> None:
        transaction = self._active_transaction
        if self._creating_angle() and transaction.target.index == AnglePointIndex.VERTEX:
            if point_distance(transaction.draft.points[0], transaction.draft.points[1]) <= 1e-6:
                return
            transaction.target = MeasurementEditTarget(EditTargetKind.CONTROL_POINT, AnglePointIndex.END)
            self.activeTransactionChanged.emit()
            return
        operation = self._operation(transaction.draft)
        measurement = operation.commit(transaction.draft)
        if not operation.is_valid(measurement):
            if not self._creating_angle():
                self.cancel_transaction()
            return
        self._measurements[measurement.measurement_id] = measurement
        self._measurement_frames[measurement.measurement_id] = self._frame_key
        self._selected_measurement_id = measurement.measurement_id
        self._active_transaction = None
        self._drag_reference = None
        self._drag_start = None
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def cancel_transaction(self) -> None:
        transaction = self._active_transaction
        if transaction is None:
            return
        self._selected_measurement_id = (transaction.draft.measurement_id
                                         if isinstance(transaction, EditMeasurementTransaction) else None)
        self._active_transaction = None
        self._drag_reference = None
        self._drag_start = None
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def clear_selection(self) -> None:
        if self._selected_measurement_id is not None:
            self._selected_measurement_id = None
            self.selectionChanged.emit()

    def clear_all(self) -> None:
        self._measurements.clear()
        self._measurement_frames.clear()
        self._active_transaction = None
        self._drag_reference = None
        self._drag_start = None
        self._selected_measurement_id = None
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def delete_selected(self) -> None:
        self.cancel_transaction()
        if self._selected_measurement_id is not None:
            self._measurements.pop(self._selected_measurement_id, None)
            self._measurement_frames.pop(self._selected_measurement_id, None)
            self.clear_selection()
            self.measurementsChanged.emit()

    def select(self, hit: MeasurementHit) -> None:
        if hit.measurement_id in self._measurements and hit.measurement_id != self._selected_measurement_id:
            self._selected_measurement_id = hit.measurement_id
            self.selectionChanged.emit()

    @Slot("QVariantList")
    def setLabelHitRegions(self, regions: list[dict]) -> None:
        """输入事件前接收 QML 实际标签矩形；整体替换，避免保留已经移走的标签。"""
        self._label_regions.clear()
        for region in regions:
            try:
                label = MeasurementLabelRegion(
                    measurement_id=str(region["measurementId"]),
                    x=float(region["x"]), y=float(region["y"]),
                    width=float(region["width"]), height=float(region["height"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            self._label_regions[label.measurement_id] = label

    def _hit_test_candidates(self, slice_index: int) -> list[Measurement]:
        """只检测当前切面；距离相同时优先选中项，其次是后绘制的图形。"""
        candidates = [
            measurement for measurement in reversed(tuple(self._measurements.values()))
            if measurement.slice_index == slice_index and self._visible(measurement)
        ]
        return sorted(candidates, key=lambda measurement:
                      measurement.measurement_id != self._selected_measurement_id)

    def hit_test(
        self,
        point: ImagePoint,
        *,
        slice_index: int,
        endpoint_tolerance: float,
        line_tolerance: float,
        viewport_point: Point | None = None,
    ) -> MeasurementHit | None:
        """按部位优先级选择命中，不在这里执行编辑动作。

        顺序：控制点 > 标签 > 轮廓 > ROI 内部。是否选中不影响内部是否命中。
        point 和两个容差使用图像像素；viewport_point 仅用于标签的视口矩形。
        返回 target.kind 标明部位，target.index 标明控制点/直线边编号。
        """
        measurements = self._hit_test_candidates(slice_index)

        # 1. 控制点负责调整形状，优先于其附近的轮廓和标签。
        control_hit = nearest_hit(
            hit_test_control_points(measurement, point, endpoint_tolerance)
            for measurement in measurements
        )
        if control_hit is not None:
            return control_hit

        # 2. 标签按屏幕矩形包含关系判断，不与图像像素距离混算。
        if viewport_point is not None:
            for measurement in measurements:
                region = self._label_regions.get(measurement.measurement_id)
                if region is not None:
                    label_hit = hit_test_label(region, viewport_point)
                    if label_hit is not None:
                        return label_hit

        # 3. 所有图形统一叫 OUTLINE；矩形边不再被误称为 BODY。
        outline_hit = nearest_hit(
            hit_test_outline(measurement, point, line_tolerance)
            for measurement in measurements
        )
        if outline_hit is not None:
            return outline_hit

        # 4. 内部命中与选择状态无关，否则未选中 ROI 无法通过内部点击被选中。
        # 多个 ROI 重叠时，沿用选中项优先、其次后绘制项优先的候选顺序。
        for measurement in measurements:
            interior_hit = hit_test_interior(measurement, point)
            if interior_hit is not None:
                return interior_hit
        return None

    def _begin_create_transaction(self, *, point: ImagePoint, context: MeasureContext) -> None:
        operations = {MeasurementKind.LENGTH: self._length_operation,
                      MeasurementKind.ANGLE: self._angle_operation,
                      MeasurementKind.RECT: self._roi_operation,
                      MeasurementKind.ELLIPSE: self._roi_operation}
        draft = operations[context.measurement_kind].create_draft(point=point, context=context)
        endpoint = 2 if isinstance(draft, RoiMeasurementDraft) else 1
        self._active_transaction = CreateMeasurementTransaction(
            context=context, draft=draft,
            target=MeasurementEditTarget(EditTargetKind.CONTROL_POINT, endpoint),
        )
        self._selected_measurement_id = None
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def _begin_edit_transaction(self, *, hit: MeasurementHit, context: MeasureContext) -> None:
        measurement = self._measurements[hit.measurement_id]
        draft = self._operation(measurement).create_edit_draft(measurement)
        self._selected_measurement_id = measurement.measurement_id
        self._active_transaction = EditMeasurementTransaction(context=context, draft=draft, target=hit.target)
        # 编辑期间只显示草稿，提交或取消后再恢复正式图形。
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()
