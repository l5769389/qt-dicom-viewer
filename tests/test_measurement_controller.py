from qt_dicom_viewer.model import (
    DragUpdateEvent,
    ImageGeometryMeta,
    ImagePoint,
    MeasureContext,
    MeasurementKind,
    Offset,
    PixelSpacing,
    Point,
    PointerPosition,
)
from qt_dicom_viewer.ui.controller.viewport.controller.measure.measure_controller import (
    MeasurementController,
)


def _context() -> MeasureContext:
    return MeasureContext(
        measurement_kind=MeasurementKind.LENGTH,
        series_uid="series-1",
        sop_instance_uid="instance-1",
        slice_index=3,
        geometry=ImageGeometryMeta(
            rows=512,
            columns=512,
            pixel_spacing=PixelSpacing(
                row=1.0,
                column=1.0,
            ),
            image_position_patient=None,
            image_orientation_patient=None,
        ),
        endpoint_tolerance=3.0,
        line_tolerance=2.0,
    )


def _position(column: float, row: float) -> PointerPosition:
    return PointerPosition(
        viewport=Point(x=column, y=row),
        image=ImagePoint(column=column, row=row),
    )


def _drag(
    start: PointerPosition,
    current: PointerPosition,
) -> DragUpdateEvent:
    return DragUpdateEvent(
        start_position=start,
        current_position=current,
        step_offset=Offset(
            x=current.viewport.x - start.viewport.x,
            y=current.viewport.y - start.viewport.y,
        ),
        total_offset=Offset(
            x=current.viewport.x - start.viewport.x,
            y=current.viewport.y - start.viewport.y,
        ),
    )


def _create_length(
    controller: MeasurementController,
) -> str:
    start = _position(0.0, 0.0)
    end = _position(10.0, 0.0)

    controller.begin(start, _context())
    controller.update(_drag(start, end))
    controller.end(end)

    items = controller.measurementItems
    assert len(items) == 1
    assert items[0]["label"] == "10.0 mm"
    return items[0]["measurementId"]


def test_create_transaction_commits_and_remains_selected() -> None:
    controller = MeasurementController()

    measurement_id = _create_length(controller)

    assert controller.activeTransaction == {}
    assert controller.selectedMeasurementId == measurement_id


def test_edit_transaction_hides_original_and_overwrites_on_commit() -> None:
    controller = MeasurementController()
    measurement_id = _create_length(controller)

    start = _position(10.0, 0.0)
    end = _position(15.0, 0.0)

    controller.begin(start, _context())

    assert controller.measurementItems == []
    assert (
        controller.activeTransaction["measurementId"]
        == measurement_id
    )

    controller.update(_drag(start, end))
    controller.end(end)

    assert controller.measurementItems[0]["label"] == "15.0 mm"
    assert controller.selectedMeasurementId == measurement_id


def test_cancel_edit_discards_draft_and_preserves_committed_data() -> None:
    controller = MeasurementController()
    measurement_id = _create_length(controller)

    start = _position(10.0, 0.0)
    end = _position(20.0, 0.0)

    controller.begin(start, _context())
    controller.update(_drag(start, end))
    controller.cancel_transaction()

    assert controller.activeTransaction == {}
    assert controller.measurementItems[0]["label"] == "10.0 mm"
    assert controller.selectedMeasurementId == measurement_id


def test_tap_empty_space_clears_selection() -> None:
    controller = MeasurementController()
    _create_length(controller)

    controller.tap_at(
        ImagePoint(column=100.0, row=100.0),
        slice_index=3,
        endpoint_tolerance=3.0,
        line_tolerance=2.0,
    )

    assert controller.selectedMeasurementId == ""
