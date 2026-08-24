import logging
from dataclasses import replace

from PySide6.QtCore import QObject, Signal, Property

from qt_dicom_viewer.model import Point, InteractionType
from qt_dicom_viewer.model.measure import LengthMeasurement, LengthMeasurementDraft

logger = logging.getLogger(__name__)


def _is_valid_for_commit(
        measurement: LengthMeasurement,
) -> bool:
    if measurement.length_mm is None or measurement.length_mm < 1.0:
        return False
    return True


class MeasurementController(QObject):
    measurementsChanged = Signal()
    draftChanged = Signal()
    selectedMeasurementChanged = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._measurements: dict[str, LengthMeasurement] = {}
        self._draft: LengthMeasurementDraft | None = None
        self._selected_measurement_id: str | None = None

    @Property("QVariantList", notify=measurementsChanged)
    def measurementItems(self) -> list[dict]:
        return [
            self._to_qml_item(measurement)
            for measurement in self._measurements.values()
        ]

    @Property("QVariantMap", notify=draftChanged)
    def draftItem(self) -> dict:
        if self._draft is None:
            return {}

        return self._to_qml_item(self._draft)

    @staticmethod
    def _to_qml_item(
            measurement: LengthMeasurement | LengthMeasurementDraft,
    ) -> dict:
        return {
            "measurementId": measurement.measurement_id,
            "type": "length",
            "startColumn": measurement.start.column,
            "startRow": measurement.start.row,
            "endColumn": measurement.end.column,
            "endRow": measurement.end.row,
            "label": (
                f"{measurement.length_mm:.1f} mm"
                if measurement.length_mm is not None
                else "--"
            ),
        }

    def update_draft(
            self,
            draft: LengthMeasurementDraft,
    ):
        self._selected_measurement_id = draft.measurement_id
        self._draft = replace(draft)
        self.draftChanged.emit()

    def change_selected_measurement(self, commit: LengthMeasurement):
        if self._selected_measurement_id == commit.measurement_id:
            return
        self._selected_measurement_id = commit.measurement_id
        self._draft = LengthMeasurementDraft(
            measurement_id=commit.measurement_id,
            series_uid=commit.series_uid,
            sop_instance_uid=commit.sop_instance_uid,
            slice_index=commit.slice_index,
            start=commit.start,
            end=commit.end,
            length_mm=commit.length_mm,
        )
        self.selectedMeasurementChanged.emit()

    def try_commit(self, commit: LengthMeasurement) -> bool | None:
        if self._draft is None or self._draft.measurement_id != commit.measurement_id:
            logger.warning(f'Adding new measurement error {commit.measurement_id}')
            return
        if not _is_valid_for_commit(commit):
            self.clear_draft()
            return
        self._measurements[self._draft.measurement_id] = commit
        self.clear_draft()
        self.measurementsChanged.emit()
        self.selectedMeasurementChanged.emit()

    def cancel_draft(self) -> None:
        self._draft = None
        self._selected_measurement_id = None
        self.draftChanged.emit()


    def clear_draft(self):
        self._draft = None
        self._selected_measurement_id = ''
        self.draftChanged.emit()
