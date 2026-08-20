from qt_dicom_viewer.model import (
    SeriesDisplayMeta,
    ViewportConfig,
)
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import (
    ViewportController,
)


def _controller() -> ViewportController:
    series_meta = SeriesDisplayMeta(
        patient_name="Example Patient",
        patient_id="P001",
        study_description="Study",
        series_description="Series",
        modality="CT",
        series_uid="series-1",
    )
    return ViewportController(
        viewport_config=ViewportConfig(
            viewport_id="viewport-1",
            tab_id="tab-1",
            viewport_type="2d",
            series_uid=series_meta.series_uid,
            series_meta=series_meta,
        ),
        tool_controller=ToolController(),
    )


def test_rotation_actions_are_normalized_to_one_turn() -> None:
    controller = _controller()

    controller.applyTransformAction("rotate:cw90")
    assert controller.rotationDegrees == 90.0

    controller.applyTransformAction("rotate:cw90")
    assert controller.rotationDegrees == 180.0

    controller.applyTransformAction("rotate:ccw90")
    assert controller.rotationDegrees == 90.0

    controller.applyTransformAction("rotate:ccw90")
    assert controller.rotationDegrees == 0.0

    controller.applyTransformAction("rotate:ccw90")
    assert controller.rotationDegrees == 270.0


def test_mirror_actions_toggle_independently() -> None:
    controller = _controller()

    controller.applyTransformAction("rotate:mirror-h")
    assert controller.horizontalFlip is True
    assert controller.verticalFlip is False

    controller.applyTransformAction("rotate:mirror-v")
    assert controller.horizontalFlip is True
    assert controller.verticalFlip is True

    controller.applyTransformAction("rotate:mirror-h")
    assert controller.horizontalFlip is False
    assert controller.verticalFlip is True


def test_unknown_transform_action_is_ignored() -> None:
    controller = _controller()
    initial_state = controller.viewport_state

    controller.applyTransformAction("rotate:unsupported")

    assert controller.viewport_state == initial_state
