import logging
import math

from PySide6.QtCore import QObject, Property, Signal

from qt_dicom_viewer.model import DragUpdateEvent, ImagePoint, PointerPosition
from qt_dicom_viewer.model.interaction import OperationStartContext
from qt_dicom_viewer.model.measure import (
    AngleMeasurement,
    AngleMeasurementDraft,
    CreateMeasurementTransaction,
    EditMeasurementTransaction,
    EditTargetKind,
    LengthMeasurement,
    LengthMeasurementDraft,
    LinePointIndex,
    MeasureContext,
    Measurement,
    MeasurementDraft,
    MeasurementEditTarget,
    MeasurementHit,
    MeasurementKind,
    MeasurementTransaction,
)
from qt_dicom_viewer.ui.controller.viewport.operation.length_measure_operation import (
    LengthMeasureOperation,
)

logger = logging.getLogger(__name__)


class MeasurementController(QObject):
    measurementsChanged = Signal()
    activeTransactionChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._measurements: dict[str, Measurement] = {}
        self._active_transaction: MeasurementTransaction | None = None
        self._selected_measurement_id: str | None = None
        self._length_operation = LengthMeasureOperation()

    @Property("QVariantList", notify=measurementsChanged)
    def measurementItems(self) -> list[dict]:
        editing_id = None
        if isinstance(
            self._active_transaction,
            EditMeasurementTransaction,
        ):
            editing_id = (
                self._active_transaction.draft.measurement_id
            )

        return [
            self._to_qml_item(measurement)
            for measurement_id, measurement
            in self._measurements.items()
            if measurement_id != editing_id
        ]

    @Property("QVariantMap", notify=activeTransactionChanged)
    def activeTransaction(self) -> dict:
        transaction = self._active_transaction
        if transaction is None:
            return {}
        return self._to_qml_item(transaction.draft)

    @Property(str, notify=selectionChanged)
    def selectedMeasurementId(self) -> str:
        return self._selected_measurement_id or ""

    @property
    def has_active_transaction(self) -> bool:
        return self._active_transaction is not None

    @staticmethod
    def _to_qml_item(
        measurement: Measurement | MeasurementDraft,
    ) -> dict:
        match measurement:
            case LengthMeasurement() | LengthMeasurementDraft():
                return {
                    "measurementId": measurement.measurement_id,
                    "type": MeasurementKind.LENGTH.value,
                    "startColumn": measurement.points[0].column,
                    "startRow": measurement.points[0].row,
                    "endColumn": measurement.points[1].column,
                    "endRow": measurement.points[1].row,
                    "label": f"{measurement.length_mm:.1f} mm",
                }

            case AngleMeasurement() | AngleMeasurementDraft():
                return {
                    "measurementId": measurement.measurement_id,
                    "type": MeasurementKind.ANGLE.value,
                    "points": [
                        {
                            "column": point.column,
                            "row": point.row,
                        }
                        for point in measurement.points
                    ],
                    "label": f"{measurement.angle:.1f}°",
                }


    def tap_at(
        self,
        point: ImagePoint | None,
        *,
        slice_index: int,
        endpoint_tolerance: float,
        line_tolerance: float,
    ) -> None:
        if self._active_transaction is not None:
            self.cancel_transaction()

        hit = None
        if point is not None:
            hit = self.hit_test(
                point,
                slice_index=slice_index,
                endpoint_tolerance=endpoint_tolerance,
                line_tolerance=line_tolerance,
            )

        selected_id = (
            hit.measurement_id
            if hit is not None
            else None
        )
        if selected_id == self._selected_measurement_id:
            return

        self._selected_measurement_id = selected_id
        self.selectionChanged.emit()

    def begin(
        self,
        position: PointerPosition,
        context: OperationStartContext | None,
    ) -> None:
        if not isinstance(context, MeasureContext):
            raise TypeError(
                "MeasurementController requires MeasureContext"
            )

        point = position.image
        if point is None:
            return

        if self._active_transaction is not None:
            self.cancel_transaction()

        hit = self.hit_test(
            point,
            slice_index=context.slice_index,
            endpoint_tolerance=context.endpoint_tolerance,
            line_tolerance=context.line_tolerance,
        )

        if hit is None:
            self._begin_create_transaction(
                point=point,
                context=context,
            )
        else:
            self._begin_edit_transaction(
                hit=hit,
                context=context,
            )

        return None

    def update(
        self,
        drag_event: DragUpdateEvent,
    ) -> None:
        transaction = self._active_transaction
        if transaction is None:
            return None

        draft = transaction.draft
        match draft:
            case LengthMeasurementDraft():
                transaction.draft = (
                    self._length_operation.update_draft(
                        draft=draft,
                        target=transaction.target,
                        drag_event=drag_event,
                        context=transaction.context,
                    )
                )

            case AngleMeasurementDraft():
                logger.warning(
                    "Angle measurement editing is not implemented"
                )
                return None

        self.activeTransactionChanged.emit()
        return None

    def end(
        self,
        position: PointerPosition,
    ) -> None:
        transaction = self._active_transaction
        if transaction is None:
            return None

        draft = transaction.draft
        match draft:
            case LengthMeasurementDraft():
                measurement = self._length_operation.commit(draft)
                if not self._length_operation.is_valid(measurement):
                    self.cancel_transaction()
                    return None


            case AngleMeasurementDraft():
                logger.warning(
                    "Angle measurement commit is not implemented"
                )
                self.cancel_transaction()
                return None

        self._measurements[
            measurement.measurement_id
        ] = measurement
        self._selected_measurement_id = None
        self._active_transaction = None

        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()
        return None

    def cancel_transaction(self) -> None:
        transaction = self._active_transaction
        if transaction is None:
            return

        if isinstance(
            transaction,
            CreateMeasurementTransaction,
        ):
            self._selected_measurement_id = None
        else:
            self._selected_measurement_id = (
                transaction.draft.measurement_id
            )

        self._active_transaction = None
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def clear_selection(self) -> None:
        if self._selected_measurement_id is None:
            return
        self._selected_measurement_id = None
        self.selectionChanged.emit()

    def delete_selected(self) -> None:
        if self._active_transaction is not None:
            self.cancel_transaction()

        measurement_id = self._selected_measurement_id
        if measurement_id is None:
            return

        self._measurements.pop(measurement_id, None)
        self._selected_measurement_id = None
        self.measurementsChanged.emit()
        self.selectionChanged.emit()

    def select(self, hit: MeasurementHit) -> None:
        if hit.measurement_id not in self._measurements:
            return
        if hit.measurement_id == self._selected_measurement_id:
            return
        self._selected_measurement_id = hit.measurement_id
        self.selectionChanged.emit()

    def hit_test(
        self,
        point: ImagePoint,
        *,
        slice_index: int,
        endpoint_tolerance: float,
        line_tolerance: float,
    ) -> MeasurementHit | None:
        best_control_hit: MeasurementHit | None = None
        best_segment_hit: MeasurementHit | None = None

        for measurement in reversed(
            tuple(self._measurements.values())
        ):
            if measurement.slice_index != slice_index:
                continue

            points = measurement.points
            if len(points) < 2:
                continue

            for point_index, control_point in enumerate(points):
                distance = point_distance(
                    point,
                    control_point,
                )
                if distance > endpoint_tolerance:
                    continue

                hit = MeasurementHit(
                    measurement_id=measurement.measurement_id,
                    target=MeasurementEditTarget(
                        kind=EditTargetKind.CONTROL_POINT,
                        index=point_index,
                    ),
                    distance=distance,
                )
                if (
                    best_control_hit is None
                    or hit.distance < best_control_hit.distance
                ):
                    best_control_hit = hit

            for segment_index in range(len(points) - 1):
                distance = point_to_segment_distance(
                    point,
                    points[segment_index],
                    points[segment_index + 1],
                )
                if distance > line_tolerance:
                    continue

                hit = MeasurementHit(
                    measurement_id=measurement.measurement_id,
                    target=MeasurementEditTarget(
                        kind=EditTargetKind.SEGMENT,
                        index=segment_index,
                    ),
                    distance=distance,
                )
                if (
                    best_segment_hit is None
                    or hit.distance < best_segment_hit.distance
                ):
                    best_segment_hit = hit

        return best_control_hit or best_segment_hit

    def _begin_create_transaction(
        self,
        *,
        point: ImagePoint,
        context: MeasureContext,
    ) -> None:
        if context.measurement_kind != MeasurementKind.LENGTH:
            logger.warning(
                "Measurement creation is not implemented for %s",
                context.measurement_kind,
            )
            return

        draft = self._length_operation.create_draft(
            point=point,
            context=context,
        )
        self._active_transaction = (
            CreateMeasurementTransaction(
                context=context,
                draft=draft,
                target=MeasurementEditTarget(
                    kind=EditTargetKind.CONTROL_POINT,
                    index=LinePointIndex.END,
                ),
            )
        )
        self._selected_measurement_id = None
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()

    def _begin_edit_transaction(
        self,
        *,
        hit: MeasurementHit,
        context: MeasureContext,
    ) -> None:
        measurement = self._measurements.get(
            hit.measurement_id
        )
        if not isinstance(
            measurement,
            LengthMeasurement,
        ):
            logger.warning(
                "Measurement editing is not implemented for %s",
                type(measurement).__name__,
            )
            return

        draft = self._length_operation.create_edit_draft(
            measurement
        )
        self._selected_measurement_id = (
            measurement.measurement_id
        )
        self._active_transaction = EditMeasurementTransaction(
            context=context,
            draft=draft,
            target=hit.target,
        )

        # Hide the committed item while its draft is displayed.
        self.measurementsChanged.emit()
        self.activeTransactionChanged.emit()
        self.selectionChanged.emit()


def point_to_segment_distance(
    point: ImagePoint,
    start: ImagePoint,
    end: ImagePoint,
) -> float:
    segment_column = end.column - start.column
    segment_row = end.row - start.row
    point_column = point.column - start.column
    point_row = point.row - start.row
    segment_length_squared = (
        segment_column * segment_column
        + segment_row * segment_row
    )

    if segment_length_squared == 0:
        return point_distance(point, start)

    projection = (
        point_column * segment_column
        + point_row * segment_row
    ) / segment_length_squared
    projection = max(0.0, min(1.0, projection))

    nearest_column = (
        start.column + projection * segment_column
    )
    nearest_row = start.row + projection * segment_row

    return math.hypot(
        point.column - nearest_column,
        point.row - nearest_row,
    )


def point_distance(
    first: ImagePoint,
    second: ImagePoint,
) -> float:
    return math.hypot(
        first.column - second.column,
        first.row - second.row,
    )
